"""
Cricket Shorts Database Models & SQLite Operations
Maintains content history, duplicate prevention, verification records, and publication tracking.
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DB_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "cricket_facts.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_DEFAULT_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables with indexes."""
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

            # Shorts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id INTEGER NOT NULL UNIQUE,
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
            conn.commit()

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

    def insert_fact(self, fact_data: Dict[str, Any]) -> Optional[int]:
        """Insert a researched and verified fact. Returns fact ID or None if duplicate."""
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
                return None

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
        """Record a generated short."""
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
            cursor.execute("""
            UPDATE shorts
            SET youtube_video_id = ?, scheduled_publish_time = ?, upload_status = 'SCHEDULED'
            WHERE id = ?
            """, (youtube_video_id, scheduled_time, short_id))
            conn.commit()

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

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status IN ('SCHEDULED', 'PUBLISHED')")
            uploaded_shorts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status = 'QC_PASSED'")
            pending_uploads = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM shorts WHERE upload_status = 'QC_FAILED'")
            failed_qc = cursor.fetchone()[0]

            # Recent shorts
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
                "uploaded_shorts": uploaded_shorts,
                "pending_uploads": pending_uploads,
                "failed_qc": failed_qc,
                "recent_shorts": recent_shorts
            }
