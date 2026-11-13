"""
Cricket Shorts Database Models & SQLite Operations
Maintains content history, duplicate prevention, verification records,
topic registry, and publication tracking with multi-layer deduplication.
"""

import sqlite3
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os

logger = logging.getLogger("cricket_shorts.database")

DB_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "cricket_facts.db")
LEDGER_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "published_topics_ledger.jsonl")


class DatabaseManager:
    def __init__(self, db_path: str = DB_DEFAULT_PATH, ledger_path: str = LEDGER_DEFAULT_PATH):
        self.db_path = db_path
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()
        self.sync_ledger_with_db()

    @contextmanager
    def get_connection(self):
        """
        Thread-safe, leak-proof SQLite connection context manager.
        - Guarantees conn.close() executes in finally block under all circumstances.
        - Enforces PRAGMA foreign_keys = ON and PRAGMA busy_timeout = 5000 before execution.
        - Automatically commits on normal exit, rolls back on exception.
        """
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            with conn:
                yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize database tables with indexes and safe migrations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Facts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_hash TEXT UNIQUE NOT NULL,
                topic TEXT NOT NULL,
                category TEXT NOT NULL,
                main_fact TEXT NOT NULL,
                source_primary TEXT NOT NULL,
                source_secondary TEXT,
                verification_notes TEXT,
                reliability_score REAL NOT NULL,
                uniqueness_score REAL NOT NULL,
                curiosity_score REAL NOT NULL,
                visual_score REAL NOT NULL,
                total_score REAL NOT NULL,
                is_approved INTEGER DEFAULT 0,
                status TEXT DEFAULT 'DISCOVERED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Safe migration for shorts table: Remove UNIQUE constraint on fact_id to prevent overwrite bugs
            try:
                table_def = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='shorts'").fetchone()
                if table_def and "fact_id INTEGER NOT NULL UNIQUE" in table_def[0]:
                    logger.info("Migrating shorts table to remove restrictive UNIQUE constraint on fact_id...")
                    cursor.execute("""
                    CREATE TABLE shorts_migration_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fact_id INTEGER NOT NULL,
                        title TEXT, hook TEXT, story TEXT, surprise TEXT, cta TEXT,
                        full_script TEXT, description TEXT, tags TEXT, hashtags TEXT,
                        pinned_comment TEXT, audio_file TEXT, subtitles_file TEXT,
                        video_file TEXT, duration_seconds REAL, qc_passed INTEGER DEFAULT 0,
                        qc_notes TEXT, upload_status TEXT DEFAULT 'PENDING',
                        youtube_video_id TEXT, scheduled_publish_time TEXT,
                        published_at TIMESTAMP, error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (fact_id) REFERENCES facts(id)
                    )
                    """)
                    cursor.execute("INSERT INTO shorts_migration_temp SELECT * FROM shorts")
                    cursor.execute("DROP TABLE shorts")
                    cursor.execute("ALTER TABLE shorts_migration_temp RENAME TO shorts")
                    logger.info("Shorts table successfully migrated.")
            except Exception as e:
                logger.warning(f"Shorts migration check notice: {e}")

            # Shorts table (without UNIQUE on fact_id)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id INTEGER NOT NULL,
                title TEXT,
                hook TEXT,
                story TEXT,
                surprise TEXT,
                cta TEXT,
                full_script TEXT,
                description TEXT,
                tags TEXT,
                hashtags TEXT,
                pinned_comment TEXT,
                audio_file TEXT,
                subtitles_file TEXT,
                video_file TEXT,
                duration_seconds REAL,
                qc_passed INTEGER DEFAULT 0,
                qc_notes TEXT,
                upload_status TEXT DEFAULT 'PENDING',
                youtube_video_id TEXT,
                scheduled_publish_time TEXT,
                published_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fact_id) REFERENCES facts(id)
            )
            """)

            # Topic Registry table for centralized deduplication & concurrency locking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_key TEXT UNIQUE NOT NULL,
                topic_title TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                category TEXT NOT NULL,
                core_concept TEXT,
                key_entities TEXT,
                key_facts TEXT,
                status TEXT DEFAULT 'AVAILABLE',
                reservation_token TEXT,
                reserved_at TIMESTAMP,
                published_at TIMESTAMP,
                youtube_video_ids TEXT,
                sha256_fingerprint TEXT,
                source TEXT DEFAULT 'CURATED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Daily execution logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                facts_researched INTEGER DEFAULT 0,
                facts_approved INTEGER DEFAULT 0,
                videos_generated INTEGER DEFAULT 0,
                videos_uploaded INTEGER DEFAULT 0,
                status TEXT DEFAULT 'RUNNING',
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create indexes for fast lookup and duplicate checks
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_hash ON facts(fact_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_status ON facts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shorts_status ON shorts(upload_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shorts_fact_id ON shorts(fact_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_reg_status ON topic_registry(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_reg_norm_title ON topic_registry(normalized_title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_reg_fingerprint ON topic_registry(sha256_fingerprint)")
            conn.commit()

            # V004 Migration: Rights-Safe Media Assets Registry & Short-Asset Junction
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Ensure clean transaction state before explicit migration transaction
            if conn.in_transaction:
                conn.commit()

            cursor.execute("BEGIN IMMEDIATE TRANSACTION;")
            try:
                v004_applied = cursor.execute(
                    "SELECT id FROM schema_migrations WHERE version = 'V004'"
                ).fetchone()

                if v004_applied:
                    cursor.execute("COMMIT;")
                    logger.debug("V004 migration already applied, skipping.")
                else:
                    logger.info("Applying V004 migration: Creating media_assets and short_asset_junction tables atomically...")

                    # 1. Media Assets Table
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media_assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_hash TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        source_platform TEXT NOT NULL,
                        license_type TEXT NOT NULL,
                        license_url TEXT NOT NULL,
                        rights_holder TEXT NOT NULL,
                        attribution_text TEXT NOT NULL,
                        is_derivative_permitted INTEGER NOT NULL DEFAULT 1 CHECK (is_derivative_permitted IN (0, 1)),
                        is_commercial_permitted INTEGER NOT NULL DEFAULT 1 CHECK (is_commercial_permitted IN (0, 1)),
                        verification_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (verification_status IN ('PENDING', 'APPROVED', 'REJECTED')),
                        verification_notes TEXT,
                        verified_by TEXT,
                        verified_at TIMESTAMP,
                        local_storage_path TEXT,
                        duration_seconds REAL CHECK (duration_seconds IS NULL OR duration_seconds >= 0.0),
                        resolution_width INTEGER CHECK (resolution_width IS NULL OR resolution_width > 0),
                        resolution_height INTEGER CHECK (resolution_height IS NULL OR resolution_height > 0),
                        fps REAL CHECK (fps IS NULL OR fps > 0.0),
                        shot_type TEXT,
                        player_names TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_assets_status ON media_assets(verification_status);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_assets_license ON media_assets(license_type);")

                    # 2. Short to Asset Junction Table
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS short_asset_junction (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        short_id INTEGER NOT NULL,
                        asset_id INTEGER NOT NULL,
                        segment_index INTEGER NOT NULL CHECK (segment_index >= 1),
                        in_point_seconds REAL NOT NULL DEFAULT 0.0 CHECK (in_point_seconds >= 0.0),
                        out_point_seconds REAL NOT NULL DEFAULT 0.0 CHECK (out_point_seconds >= 0.0),
                        applied_motion_profile TEXT DEFAULT 'CENTER_MOTION',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (short_id) REFERENCES shorts(id) ON DELETE CASCADE,
                        FOREIGN KEY (asset_id) REFERENCES media_assets(id) ON DELETE RESTRICT,
                        CHECK (out_point_seconds >= in_point_seconds)
                    );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_junction_short_id ON short_asset_junction(short_id);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_junction_asset_id ON short_asset_junction(asset_id);")
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_junction_short_segment ON short_asset_junction(short_id, segment_index);")

                    # 3. Record migration in ledger
                    cursor.execute(
                        "INSERT INTO schema_migrations (version, description) VALUES ('V004', 'Add media_assets and short_asset_junction');"
                    )

                    cursor.execute("COMMIT;")
                    logger.info("V004 migration applied successfully and committed atomically.")
            except Exception as ex:
                cursor.execute("ROLLBACK;")
                logger.error(f"V004 migration failed and was rolled back completely: {ex}")
                raise RuntimeError(f"V004 migration failed and was rolled back: {ex}") from ex

    def sync_ledger_with_db(self):
        """
        Synchronizes historical published topics between published_topics_ledger.jsonl
        and SQLite topic_registry to ensure 100% persistence across git and environments.
        """
        if not os.path.exists(self.ledger_path):
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        entry = json.loads(line)
                        t_key = entry.get("topic_key")
                        if not t_key:
                            continue

                        # Check if exists in registry
                        existing = cursor.execute("SELECT id, status, youtube_video_ids FROM topic_registry WHERE topic_key = ?", (t_key,)).fetchone()
                        yt_ids = json.dumps(entry.get("youtube_video_ids", []))
                        key_entities = json.dumps(entry.get("key_entities", []))
                        key_facts = json.dumps(entry.get("key_facts", []))

                        if not existing:
                            cursor.execute("""
                            INSERT INTO topic_registry (
                                topic_key, topic_title, normalized_title, category,
                                core_concept, key_entities, key_facts, status,
                                published_at, youtube_video_ids, sha256_fingerprint, source
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                t_key,
                                entry.get("topic_title", t_key),
                                entry.get("normalized_title", t_key.lower()),
                                entry.get("category", "General"),
                                entry.get("core_concept", ""),
                                key_entities,
                                key_facts,
                                entry.get("status", "PUBLISHED"),
                                entry.get("last_published_at", entry.get("first_published_at")),
                                yt_ids,
                                entry.get("sha256_fingerprint", ""),
                                entry.get("source", "CURATED")
                            ))
                        else:
                            # Update status to PUBLISHED if ledger says PUBLISHED
                            if entry.get("status") == "PUBLISHED" and existing["status"] != "PUBLISHED":
                                cursor.execute("""
                                UPDATE topic_registry SET
                                    status = 'PUBLISHED',
                                    published_at = ?,
                                    youtube_video_ids = ?
                                WHERE topic_key = ?
                                """, (entry.get("last_published_at"), yt_ids, t_key))
                conn.commit()
            except Exception as e:
                logger.error(f"Error syncing ledger with db: {e}")

    def append_to_ledger(self, topic_entry: Dict[str, Any]):
        """Appends a published topic record to the JSONL persistent ledger."""
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(topic_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to persistent ledger: {e}")

    @staticmethod
    def compute_fact_hash(topic: str, main_fact: str) -> str:
        """Create a normalized SHA-256 hash to strictly prevent duplicate facts."""
        normalized = f"{topic.strip().lower()}::{main_fact.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def fact_exists(self, topic: str, main_fact: str) -> bool:
        """Check if a fact or near-identical fact already exists in the database."""
        fact_hash = self.compute_fact_hash(topic, main_fact)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM facts WHERE fact_hash = ?", (fact_hash,))
            return cursor.fetchone() is not None

    def insert_fact(self, fact_data: Dict[str, Any], return_existing: bool = False) -> Optional[int]:
        """Insert a researched and verified fact. Returns fact ID, existing ID if return_existing=True, or None if duplicate."""
        fact_hash = self.compute_fact_hash(fact_data["topic"], fact_data["main_fact"])
        total_score = (
            fact_data.get("reliability_score", 0)
            + fact_data.get("uniqueness_score", 0)
            + fact_data.get("curiosity_score", 0)
            + fact_data.get("visual_score", 0)
        )
        is_approved = 1 if total_score >= 80 and fact_data.get("reliability_score", 0) >= 30 else 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO facts (
                    fact_hash, topic, category, main_fact,
                    source_primary, source_secondary, verification_notes,
                    reliability_score, uniqueness_score, curiosity_score, visual_score,
                    total_score, is_approved, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fact_hash,
                    fact_data["topic"],
                    fact_data["category"],
                    fact_data["main_fact"],
                    fact_data["source_primary"],
                    fact_data.get("source_secondary", ""),
                    fact_data.get("verification_notes", ""),
                    fact_data.get("reliability_score", 0),
                    fact_data.get("uniqueness_score", 0),
                    fact_data.get("curiosity_score", 0),
                    fact_data.get("visual_score", 0),
                    total_score,
                    is_approved,
                    "APPROVED" if is_approved else "REJECTED"
                ))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Fact already exists
                if return_existing:
                    cursor.execute("SELECT id FROM facts WHERE fact_hash = ?", (fact_hash,))
                    row = cursor.fetchone()
                    return row["id"] if row else None
                return None

    def get_fact_by_hash(self, fact_hash: str) -> Optional[int]:
        """Retrieve existing fact ID by its SHA-256 fact hash."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM facts WHERE fact_hash = ?", (fact_hash,))
            row = cursor.fetchone()
            return row["id"] if row else None

    def get_unprocessed_approved_facts(self, limit: int = 2) -> List[Dict[str, Any]]:
        """Get approved facts that haven't been turned into shorts yet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT f.* FROM facts f
            LEFT JOIN shorts s ON f.id = s.fact_id
            WHERE f.is_approved = 1 AND s.id IS NULL
            ORDER BY f.total_score DESC, f.created_at ASC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def insert_short(self, short_data: Dict[str, Any]) -> int:
        """Record a generated short without clobbering history."""
        fact_id = short_data.get("fact_id")
        if not fact_id:
            raise ValueError(f"Cannot insert short without valid fact_id: {short_data.get('title')}")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO shorts (
                fact_id, title, hook, story, surprise, cta,
                full_script, description, tags, hashtags, pinned_comment,
                audio_file, subtitles_file, video_file, duration_seconds,
                qc_passed, qc_notes, upload_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                short_data["fact_id"],
                short_data.get("title", ""),
                short_data.get("hook", ""),
                short_data.get("story", ""),
                short_data.get("surprise", ""),
                short_data.get("cta", ""),
                short_data.get("full_script", ""),
                short_data.get("description", ""),
                short_data.get("tags", ""),
                short_data.get("hashtags", ""),
                short_data.get("pinned_comment", ""),
                short_data.get("audio_file", ""),
                short_data.get("subtitles_file", ""),
                short_data.get("video_file", ""),
                short_data.get("duration_seconds", 0.0),
                short_data.get("qc_passed", 0),
                short_data.get("qc_notes", ""),
                short_data.get("upload_status", "GENERATED")
            ))
            conn.commit()
            return cursor.lastrowid

    def update_short_qc(self, short_id: int, passed: bool, notes: str, video_path: str, duration: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE shorts
            SET qc_passed = ?, qc_notes = ?, video_file = ?, duration_seconds = ?,
                upload_status = CASE WHEN ? = 1 THEN 'QC_PASSED' ELSE 'QC_FAILED' END
            WHERE id = ?
            """, (1 if passed else 0, notes, video_path, duration, 1 if passed else 0, short_id))
            conn.commit()

    def update_short_upload(self, short_id: int, youtube_video_id: str, scheduled_time: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            status = 'PUBLISHED' if not scheduled_time else 'SCHEDULED'
            cursor.execute("""
            UPDATE shorts
            SET youtube_video_id = ?, scheduled_publish_time = ?, upload_status = ?, published_at = ?
            WHERE id = ?
            """, (youtube_video_id, scheduled_time, status, now_iso, short_id))
            conn.commit()

    # --- Topic Registry & Deduplication Locking Operations ---

    def register_topic(self, topic_entry: Dict[str, Any]) -> int:
        """Inserts a candidate topic into topic_registry or updates it."""
        t_key = topic_entry["topic_key"]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute("SELECT id FROM topic_registry WHERE topic_key = ?", (t_key,)).fetchone()
            if row:
                return row[0]

            cursor.execute("""
            INSERT INTO topic_registry (
                topic_key, topic_title, normalized_title, category,
                core_concept, key_entities, key_facts, status,
                sha256_fingerprint, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t_key,
                topic_entry.get("topic_title", t_key),
                topic_entry.get("normalized_title", t_key.lower()),
                topic_entry.get("category", "General"),
                topic_entry.get("core_concept", ""),
                json.dumps(topic_entry.get("key_entities", [])),
                json.dumps(topic_entry.get("key_facts", [])),
                topic_entry.get("status", "AVAILABLE"),
                topic_entry.get("sha256_fingerprint", ""),
                topic_entry.get("source", "CURATED")
            ))
            conn.commit()
            return cursor.lastrowid

    def reserve_topic(self, topic_key: str, token: str) -> bool:
        """
        Atomically locks and reserves a topic for video generation.
        Returns True if reservation was successful, False if already reserved or published.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            # Only reserve if status is AVAILABLE or if previously FAILED
            cursor.execute("""
            UPDATE topic_registry
            SET status = 'RESERVED', reservation_token = ?, reserved_at = ?, updated_at = ?
            WHERE topic_key = ? AND status IN ('AVAILABLE', 'FAILED')
            """, (token, now_iso, now_iso, topic_key))
            conn.commit()
            return cursor.rowcount > 0

    def mark_topic_published(self, topic_key: str, youtube_id: str, topic_meta: Optional[Dict[str, Any]] = None) -> bool:
        """
        Atomically marks a topic as PUBLISHED, records the YouTube Video ID,
        and persists it to published_topics_ledger.jsonl.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()

            # Retrieve existing video IDs
            row = cursor.execute("SELECT youtube_video_ids FROM topic_registry WHERE topic_key = ?", (topic_key,)).fetchone()
            existing_ids = []
            if row and row["youtube_video_ids"]:
                try:
                    existing_ids = json.loads(row["youtube_video_ids"])
                except Exception:
                    existing_ids = [row["youtube_video_ids"]]

            if youtube_id and youtube_id not in existing_ids and not youtube_id.startswith("DRYRUN"):
                existing_ids.append(youtube_id)

            cursor.execute("""
            UPDATE topic_registry
            SET status = 'PUBLISHED', published_at = ?, youtube_video_ids = ?, updated_at = ?
            WHERE topic_key = ?
            """, (now_iso, json.dumps(existing_ids), now_iso, topic_key))
            conn.commit()

            # Append to persistent JSONL ledger
            row_full = cursor.execute("SELECT * FROM topic_registry WHERE topic_key = ?", (topic_key,)).fetchone()
            if row_full:
                ledger_record = {
                    "topic_key": topic_key,
                    "topic_title": row_full["topic_title"],
                    "normalized_title": row_full["normalized_title"],
                    "category": row_full["category"],
                    "core_concept": row_full["core_concept"],
                    "key_entities": json.loads(row_full["key_entities"]) if row_full["key_entities"] else [],
                    "key_facts": json.loads(row_full["key_facts"]) if row_full["key_facts"] else [],
                    "status": "PUBLISHED",
                    "youtube_video_ids": existing_ids,
                    "last_published_at": now_iso,
                    "sha256_fingerprint": row_full["sha256_fingerprint"],
                    "source": row_full["source"]
                }
                self.append_to_ledger(ledger_record)
            return True

    def mark_topic_failed(self, topic_key: str, error_message: str):
        """Marks a topic as FAILED so it can be investigated or released without claiming publication."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            UPDATE topic_registry
            SET status = 'FAILED', updated_at = ?
            WHERE topic_key = ? AND status = 'RESERVED'
            """, (now_iso, topic_key))
            conn.commit()

    def release_topic(self, topic_key: str) -> bool:
        """Releases a RESERVED topic back to AVAILABLE status if production was canceled."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            UPDATE topic_registry
            SET status = 'AVAILABLE', reservation_token = NULL, reserved_at = NULL, updated_at = ?
            WHERE topic_key = ? AND status = 'RESERVED'
            """, (now_iso, topic_key))
            conn.commit()
            return cursor.rowcount > 0

    def is_topic_published(self, topic_key: str) -> bool:
        """Returns True if the topic key has ever been published."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute("SELECT status FROM topic_registry WHERE topic_key = ?", (topic_key,)).fetchone()
            return row is not None and row["status"] == "PUBLISHED"

    def get_all_registered_topics(self) -> List[Dict[str, Any]]:
        """Returns all entries in the topic registry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM topic_registry ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_published_topics(self) -> List[Dict[str, Any]]:
        """Returns all topics that have been published to YouTube."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM topic_registry WHERE status = 'PUBLISHED' ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Aggregate stats for reporting and dashboard."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM facts")
            total_facts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM facts WHERE is_approved = 1")
            approved_facts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts")
            total_shorts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM topic_registry WHERE status = 'PUBLISHED'")
            published_topics_cnt = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status IN ('SCHEDULED', 'PUBLISHED')")
            uploaded_shorts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status = 'QC_PASSED'")
            pending_uploads = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status = 'QC_FAILED'")
            failed_qc = cursor.fetchone()[0]

            cursor.execute("""
            SELECT s.id, f.topic, s.title, s.upload_status, s.scheduled_publish_time, s.created_at
            FROM shorts s
            JOIN facts f ON s.fact_id = f.id
            ORDER BY s.created_at DESC
            LIMIT 5
            """)
            recent_shorts = [dict(row) for row in cursor.fetchall()]

            return {
                "total_facts": total_facts,
                "approved_facts": approved_facts,
                "total_shorts": total_shorts,
                "published_topics": published_topics_cnt,
                "uploaded_shorts": uploaded_shorts,
                "pending_uploads": pending_uploads,
                "failed_qc": failed_qc,
                "recent_shorts": recent_shorts
            }

    def register_media_asset(self, asset_data: Dict[str, Any]) -> int:
        """
        Inserts or returns existing media asset record by asset_hash.
        Enforces all schema CHECK constraints and returns the asset row ID.
        """
        asset_hash = asset_data["asset_hash"]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            existing = cursor.execute("SELECT id FROM media_assets WHERE asset_hash = ?", (asset_hash,)).fetchone()
            if existing:
                return existing["id"]

            cursor.execute("""
            INSERT INTO media_assets (
                asset_hash, title, source_url, source_platform, license_type,
                license_url, rights_holder, attribution_text, is_derivative_permitted,
                is_commercial_permitted, verification_status, verification_notes,
                verified_by, verified_at, local_storage_path, duration_seconds,
                resolution_width, resolution_height, fps, shot_type, player_names
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_hash,
                asset_data.get("title", ""),
                asset_data.get("source_url", ""),
                asset_data.get("source_platform", "UNKNOWN"),
                asset_data.get("license_type", "UNKNOWN"),
                asset_data.get("license_url", ""),
                asset_data.get("rights_holder", ""),
                asset_data.get("attribution_text", ""),
                asset_data.get("is_derivative_permitted", 1),
                asset_data.get("is_commercial_permitted", 1),
                asset_data.get("verification_status", "PENDING"),
                asset_data.get("verification_notes"),
                asset_data.get("verified_by"),
                asset_data.get("verified_at"),
                asset_data.get("local_storage_path"),
                asset_data.get("duration_seconds"),
                asset_data.get("resolution_width"),
                asset_data.get("resolution_height"),
                asset_data.get("fps"),
                asset_data.get("shot_type"),
                json.dumps(asset_data.get("player_names", [])) if isinstance(asset_data.get("player_names"), list) else asset_data.get("player_names")
            ))
            return cursor.lastrowid

    def link_short_to_asset(
        self,
        short_id: int,
        asset_id: int,
        segment_index: int,
        in_point_seconds: float = 0.0,
        out_point_seconds: float = 0.0,
        motion_profile: str = "CENTER_MOTION"
    ) -> int:
        """
        Links a short record to a verified media asset for a specific narrative segment.
        Enforces foreign key relationships and unique constraint per segment.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO short_asset_junction (
                short_id, asset_id, segment_index, in_point_seconds, out_point_seconds, applied_motion_profile
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (short_id, asset_id, segment_index, in_point_seconds, out_point_seconds, motion_profile))
            return cursor.lastrowid

    def get_short_assets(self, short_id: int) -> List[Dict[str, Any]]:
        """Retrieves all linked media assets for a given short, ordered by segment index."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT j.id as junction_id, j.segment_index, j.in_point_seconds, j.out_point_seconds,
                   j.applied_motion_profile, m.*
            FROM short_asset_junction j
            JOIN media_assets m ON j.asset_id = m.id
            WHERE j.short_id = ?
            ORDER BY j.segment_index ASC
            """, (short_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_asset_by_hash(self, asset_hash: str) -> Optional[Dict[str, Any]]:
        """Fetches a media asset record by cryptographic hash."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute("SELECT * FROM media_assets WHERE asset_hash = ?", (asset_hash,)).fetchone()
            return dict(row) if row else None
