"""
Cricket Shorts Database Backup and Restore Utility
Provides atomic, lock-safe online backups and verified offline restore operations
using native SQLite Backup API and POSIX atomic filesystem replacement.
"""

import os
import sqlite3
import shutil
import logging
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("cricket_shorts.database.backup")

CORE_TABLES = ["facts", "shorts", "topic_registry"]


def safe_online_backup(
    source_db_path: str = "database/cricket_facts.db",
    backup_dir: str = "database/backups"
) -> str:
    """
    Creates a non-blocking, transaction-safe online snapshot of the database
    using SQLite's native backup API.

    Guarantees:
    - Both source and destination connections are explicitly closed via try/finally.
    - Post-backup integrity check, foreign key check, and exact row count parity.
    - Timestamp collision protection with PID and microsecond resolution.
    - Atomic cleanup of partial file on failure (never silently succeeds).
    """
    if not os.path.exists(source_db_path):
        raise FileNotFoundError(f"Source database file not found: {source_db_path}")

    os.makedirs(backup_dir, exist_ok=True)

    # Collision-safe timestamp filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup_filename = f"cricket_facts_backup_{timestamp}_pid{os.getpid()}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    counter = 1
    while os.path.exists(backup_path):
        backup_filename = f"cricket_facts_backup_{timestamp}_pid{os.getpid()}_{counter}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        counter += 1

    src_conn = None
    dst_conn = None
    try:
        src_conn = sqlite3.connect(source_db_path, timeout=10.0)
        dst_conn = sqlite3.connect(backup_path, timeout=10.0)

        # Coordinate online lock-safe page copy
        src_conn.backup(dst_conn, pages=100)
    except Exception as e:
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except OSError:
                pass
        raise RuntimeError(f"SQLite online backup copy failed: {e}") from e
    finally:
        if dst_conn is not None:
            dst_conn.close()
        if src_conn is not None:
            src_conn.close()

    # Post-backup validation & row parity check
    verify_conn = None
    src_verify_conn = None
    try:
        verify_conn = sqlite3.connect(backup_path, timeout=10.0)
        verify_conn.row_factory = sqlite3.Row
        cur = verify_conn.cursor()

        # 1. Integrity check
        integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")

        # 2. Foreign key check
        cur.execute("PRAGMA foreign_keys = ON;")
        fk_violations = cur.execute("PRAGMA foreign_key_check;").fetchall()
        if len(fk_violations) > 0:
            raise RuntimeError(f"Backup foreign key check found {len(fk_violations)} violations!")

        # 3. Exact row count parity check against live source DB
        src_verify_conn = sqlite3.connect(source_db_path, timeout=10.0)
        src_cur = src_verify_conn.cursor()

        for table in CORE_TABLES:
            src_count = src_cur.execute(f"SELECT count(*) FROM {table};").fetchone()[0]
            dst_count = cur.execute(f"SELECT count(*) FROM {table};").fetchone()[0]
            if src_count != dst_count:
                raise RuntimeError(
                    f"Backup parity mismatch on table '{table}': source has {src_count} rows, backup has {dst_count} rows!"
                )

        # 4. Non-zero file size check
        if os.path.getsize(backup_path) <= 0:
            raise RuntimeError("Backup file size is 0 bytes!")

    except Exception as e:
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except OSError:
                pass
        raise RuntimeError(f"Backup post-verification failed: {e}") from e
    finally:
        if verify_conn is not None:
            verify_conn.close()
        if src_verify_conn is not None:
            src_verify_conn.close()

    logger.info(f"Verified database backup created successfully: {backup_path}")
    return backup_path


def check_offline_maintenance_preconditions(target_db_path: str) -> None:
    """
    Verifies that no active application or pipeline process is holding locks
    or open connections on target_db_path before an offline restore operation.

    NOTE: Passing this check verifies only that no connection holds an exclusive
    lock at this instant; it does NOT replace or substitute for explicit operator
    offline confirmation (is_offline_confirmed=True).
    """
    if not os.path.exists(target_db_path):
        return

    test_conn = None
    try:
        test_conn = sqlite3.connect(target_db_path, timeout=0.2)
        test_conn.execute("BEGIN EXCLUSIVE TRANSACTION;")
        test_conn.execute("ROLLBACK;")
    except sqlite3.OperationalError as e:
        raise RuntimeError(
            f"Offline precondition failed: Database is actively locked by another process! Error: {e}. "
            f"All application, scheduler, and CLI processes must be stopped before restore."
        ) from e
    except sqlite3.DatabaseError as e:
        raise RuntimeError(
            f"Pre-restore safety check failed: Target file '{target_db_path}' is corrupt or not a valid SQLite database: {e}"
        ) from e
    finally:
        if test_conn is not None:
            test_conn.close()


def restore_database(
    backup_path: str,
    target_db_path: str = "database/cricket_facts.db",
    is_offline_confirmed: bool = False
) -> Tuple[str, str]:
    """
    Performs an offline maintenance restoration of target_db_path from backup_path.

    Mandatory Safety Guarantees:
    1. Offline Maintenance Enforcement: Requires is_offline_confirmed=True.
       A temporary SQLite lock check is not treated as proof that processes cannot reconnect.
    2. Backup Pre-Validation: Backup file must pass integrity_check, foreign_key_check,
       and have all core tables (facts, shorts, topic_registry) before touching target.
    3. Expected Count Recording: Records exact expected row counts for facts, shorts,
       and topic_registry directly from the validated backup.
    4. Pre-Restore Safety Copy: If target database exists, creates a safety copy and
       validates it with integrity_check and foreign_key_check before any replacement.
    5. POSIX Atomic File Replacement: Copies backup to a temporary staging file on the
       exact same filesystem directory, verifies staging, and calls os.replace().
    6. Post-Restore Full Verification: Verifies integrity_check, foreign_key_check, and
       all three expected row counts on the replaced database.
    7. Automated Recovery: If post-restore verification fails, automatically rolls back
       to the validated safety copy using atomic replacement, verifies recovery, and
       reports explicit recovery status.

    Returns:
        Tuple[str, str]: (target_db_path, safety_copy_path)
    """
    # 1. Enforce offline maintenance confirmation
    if not is_offline_confirmed:
        raise RuntimeError(
            "Restore aborted: Offline maintenance mode must be explicitly confirmed. "
            "All application servers, schedulers, CLI tools, and background workers accessing "
            f"'{target_db_path}' must be completely stopped before initiating restore. "
            "Set is_offline_confirmed=True only after ensuring all processes are offline."
        )

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file does not exist: {backup_path}")

    # Check for active exclusive locks on target
    check_offline_maintenance_preconditions(target_db_path)

    # 2. Pre-validate backup file and record expected row counts
    expected_counts: Dict[str, int] = {}
    b_conn = None
    try:
        b_conn = sqlite3.connect(backup_path, timeout=10.0)
        b_cur = b_conn.cursor()

        integ = b_cur.execute("PRAGMA integrity_check;").fetchone()[0]
        if integ != "ok":
            raise RuntimeError(f"Cannot restore from corrupt backup: {integ}")

        b_cur.execute("PRAGMA foreign_keys = ON;")
        fk_violations = b_cur.execute("PRAGMA foreign_key_check;").fetchall()
        if len(fk_violations) > 0:
            raise RuntimeError(f"Cannot restore: Backup contains {len(fk_violations)} foreign key violations!")

        for table in CORE_TABLES:
            table_exists = b_cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;", (table,)
            ).fetchone()
            if not table_exists:
                raise RuntimeError(f"Cannot restore: Backup is missing required core table '{table}'!")
            count_res = b_cur.execute(f"SELECT count(*) FROM {table};").fetchone()
            expected_counts[table] = count_res[0]

    except Exception as e:
        raise RuntimeError(f"Backup pre-validation failed for '{backup_path}': {e}") from e
    finally:
        if b_conn is not None:
            b_conn.close()

    target_dir = os.path.dirname(os.path.abspath(target_db_path))
    os.makedirs(target_dir, exist_ok=True)

    # 3. Create and validate safety copy of current live database
    safety_copy_path: Optional[str] = None
    if os.path.exists(target_db_path):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        safety_copy_path = os.path.join(target_dir, f"cricket_facts_pre_restore_{timestamp}.db")
        try:
            shutil.copy2(target_db_path, safety_copy_path)
        except Exception as e:
            raise RuntimeError(f"Failed to create pre-restore safety copy: {e}") from e

        # Validate pre-restore safety copy before touching or replacing target DB
        safety_conn = None
        try:
            safety_conn = sqlite3.connect(safety_copy_path, timeout=10.0)
            s_cur = safety_conn.cursor()
            s_integ = s_cur.execute("PRAGMA integrity_check;").fetchone()[0]
            if s_integ != "ok":
                raise RuntimeError(f"Pre-restore safety copy integrity check failed: {s_integ}")
            s_cur.execute("PRAGMA foreign_keys = ON;")
            s_fks = s_cur.execute("PRAGMA foreign_key_check;").fetchall()
            if len(s_fks) > 0:
                raise RuntimeError(
                    f"Pre-restore safety copy foreign key check found {len(s_fks)} violations!"
                )
        except Exception as e:
            if os.path.exists(safety_copy_path):
                try:
                    os.remove(safety_copy_path)
                except OSError:
                    pass
            raise RuntimeError(f"Pre-restore safety copy validation failed: {e}") from e
        finally:
            if safety_conn is not None:
                safety_conn.close()

    # 4. Same-filesystem staging and POSIX atomic replacement
    temp_staging_path = os.path.join(
        target_dir, f".restore_staging_{os.getpid()}_{int(datetime.now(timezone.utc).timestamp())}.db"
    )

    try:
        shutil.copy2(backup_path, temp_staging_path)

        # Validate staging file integrity before swap
        s_conn = sqlite3.connect(temp_staging_path, timeout=10.0)
        try:
            if s_conn.execute("PRAGMA integrity_check;").fetchone()[0] != "ok":
                raise RuntimeError("Staging file failed integrity check")
            s_conn.execute("PRAGMA foreign_keys = ON;")
            if len(s_conn.execute("PRAGMA foreign_key_check;").fetchall()) > 0:
                raise RuntimeError("Staging file has foreign key violations")
        finally:
            s_conn.close()

        # Atomic replacement
        os.replace(temp_staging_path, target_db_path)

    except Exception as e:
        if os.path.exists(temp_staging_path):
            try:
                os.remove(temp_staging_path)
            except OSError:
                pass
        raise RuntimeError(f"Atomic restore operation failed during file replacement: {e}") from e

    # 5. Post-restore verification with automatic recovery on failure
    post_conn = None
    try:
        post_conn = sqlite3.connect(target_db_path, timeout=10.0)
        cur = post_conn.cursor()

        integ = cur.execute("PRAGMA integrity_check;").fetchone()[0]
        if integ != "ok":
            raise RuntimeError(f"Integrity check failed: {integ}")

        cur.execute("PRAGMA foreign_keys = ON;")
        fk_violations = cur.execute("PRAGMA foreign_key_check;").fetchall()
        if len(fk_violations) > 0:
            raise RuntimeError(f"Foreign key check found {len(fk_violations)} violations!")

        for table, exp_count in expected_counts.items():
            actual_count = cur.execute(f"SELECT count(*) FROM {table};").fetchone()[0]
            if actual_count != exp_count:
                raise RuntimeError(
                    f"Table '{table}' row count mismatch: expected {exp_count}, got {actual_count}!"
                )

    except Exception as verify_err:
        logger.error(f"Post-restore verification failed on '{target_db_path}': {verify_err}")
        if post_conn is not None:
            try:
                post_conn.close()
            except Exception:
                pass
            post_conn = None

        # Attempt automatic recovery from the validated safety copy
        if safety_copy_path and os.path.exists(safety_copy_path):
            recovery_staging = os.path.join(
                target_dir, f".recovery_staging_{os.getpid()}_{int(datetime.now(timezone.utc).timestamp())}.db"
            )
            try:
                shutil.copy2(safety_copy_path, recovery_staging)
                rec_conn = sqlite3.connect(recovery_staging, timeout=10.0)
                try:
                    if rec_conn.execute("PRAGMA integrity_check;").fetchone()[0] != "ok":
                        raise RuntimeError("Recovery staging failed integrity check")
                finally:
                    rec_conn.close()

                os.replace(recovery_staging, target_db_path)

                # Validate restored database
                rec_v_conn = sqlite3.connect(target_db_path, timeout=10.0)
                try:
                    if rec_v_conn.execute("PRAGMA integrity_check;").fetchone()[0] != "ok":
                        raise RuntimeError("Recovered database failed integrity check")
                    rec_v_conn.execute("PRAGMA foreign_keys = ON;")
                    if len(rec_v_conn.execute("PRAGMA foreign_key_check;").fetchall()) > 0:
                        raise RuntimeError("Recovered database has foreign key violations")
                finally:
                    rec_v_conn.close()

                raise RuntimeError(
                    f"Post-restore verification failed: {verify_err}. "
                    f"RECOVERY STATUS: SUCCESS. Target database was safely rolled back and restored "
                    f"from validated safety copy: '{safety_copy_path}'."
                ) from verify_err

            except Exception as rec_err:
                if os.path.exists(recovery_staging):
                    try:
                        os.remove(recovery_staging)
                    except OSError:
                        pass
                if "RECOVERY STATUS: SUCCESS" in str(rec_err):
                    raise
                raise RuntimeError(
                    f"Post-restore verification failed: {verify_err}. "
                    f"RECOVERY STATUS: FAILED. Automatic recovery from safety copy failed: {rec_err}. "
                    f"Safety copy preserved for manual recovery at: '{safety_copy_path}'."
                ) from verify_err
        else:
            raise RuntimeError(
                f"Post-restore verification failed: {verify_err}. "
                f"RECOVERY STATUS: UNAVAILABLE. No safety copy was available to recover from."
            ) from verify_err

    finally:
        if post_conn is not None:
            post_conn.close()

    logger.info(
        f"Database successfully restored from {backup_path}. "
        f"Verified counts: {expected_counts}. Safety copy: {safety_copy_path}"
    )
    return target_db_path, safety_copy_path or ""


class TestDatabaseBackupAndRestore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.source_db = os.path.join(self.temp_dir, "test_source.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.target_db = os.path.join(self.temp_dir, "test_target.db")

        # Initialize test source database with schema and sample records
        conn = sqlite3.connect(self.source_db)
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_title TEXT NOT NULL,
                sub_topic TEXT,
                narrative_text TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE shorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id INTEGER,
                title TEXT NOT NULL,
                video_id TEXT UNIQUE,
                duration INTEGER,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fact_id) REFERENCES facts(id) ON DELETE RESTRICT
            );
            CREATE TABLE topic_registry (
                topic_key TEXT PRIMARY KEY,
                topic_title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO facts (topic_title, sub_topic, narrative_text) VALUES
                ('Fact 1', 'Sub 1', 'Narrative 1'),
                ('Fact 2', 'Sub 2', 'Narrative 2');
            INSERT INTO shorts (fact_id, title, video_id, status) VALUES
                (1, 'Short 1', 'vid_001', 'published'),
                (2, 'Short 2', 'vid_002', 'published');
            INSERT INTO topic_registry (topic_key, topic_title, category, status) VALUES
                ('topic_1', 'Topic 1', 'Records', 'PUBLISHED'),
                ('topic_2', 'Topic 2', 'History', 'PUBLISHED');
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_offline_confirmation_enforced(self):
        """Verify restore raises RuntimeError if is_offline_confirmed is False."""
        backup_file = safe_online_backup(self.source_db, self.backup_dir)
        with self.assertRaises(RuntimeError) as ctx:
            restore_database(backup_file, self.target_db, is_offline_confirmed=False)
        self.assertIn("Offline maintenance mode must be explicitly confirmed", str(ctx.exception))

    def test_successful_restore_and_verification(self):
        """Verify complete restore lifecycle with pre/post verification and parity."""
        # 1. Take verified backup
        backup_file = safe_online_backup(self.source_db, self.backup_dir)

        # 2. Setup target db with different/older state (3 facts)
        shutil.copy2(self.source_db, self.target_db)
        target_conn = sqlite3.connect(self.target_db)
        target_conn.execute("INSERT INTO facts (topic_title, narrative_text) VALUES ('Extra Fact', 'Extra');")
        target_conn.commit()
        count_before = target_conn.execute("SELECT count(*) FROM facts;").fetchone()[0]
        self.assertEqual(count_before, 3)
        target_conn.close()

        # 3. Perform verified restore with offline confirmation
        restored_path, safety_copy = restore_database(
            backup_file, self.target_db, is_offline_confirmed=True
        )

        self.assertEqual(restored_path, self.target_db)
        self.assertTrue(os.path.exists(safety_copy))

        # 4. Verify restored state matches backup exactly (2 facts, 2 shorts, 2 topics)
        v_conn = sqlite3.connect(self.target_db)
        cur = v_conn.cursor()
        self.assertEqual(cur.execute("PRAGMA integrity_check;").fetchone()[0], "ok")
        v_conn.execute("PRAGMA foreign_keys = ON;")
        self.assertEqual(len(cur.execute("PRAGMA foreign_key_check;").fetchall()), 0)
        self.assertEqual(cur.execute("SELECT count(*) FROM facts;").fetchone()[0], 2)
        self.assertEqual(cur.execute("SELECT count(*) FROM shorts;").fetchone()[0], 2)
        self.assertEqual(cur.execute("SELECT count(*) FROM topic_registry;").fetchone()[0], 2)
        v_conn.close()

        # 5. Verify safety copy preserved previous state (3 facts)
        s_conn = sqlite3.connect(safety_copy)
        self.assertEqual(s_conn.execute("SELECT count(*) FROM facts;").fetchone()[0], 3)
        s_conn.close()

    def test_pre_restore_safety_check_corrupt_file(self):
        """Verify restore aborts if pre-restore safety check detects invalid/corrupt database."""
        backup_file = safe_online_backup(self.source_db, self.backup_dir)

        # Create a corrupt target database file
        with open(self.target_db, "wb") as f:
            f.write(b"NOT A VALID SQLITE DATABASE FILE HEADER CORRUPTION")

        with self.assertRaises(RuntimeError) as ctx:
            restore_database(backup_file, self.target_db, is_offline_confirmed=True)
        self.assertTrue(
            "Pre-restore" in str(ctx.exception) or "corrupt" in str(ctx.exception)
        )

    def test_pre_restore_safety_copy_foreign_key_violation(self):
        """Verify restore aborts if pre-restore target database has foreign key violations."""
        backup_file = safe_online_backup(self.source_db, self.backup_dir)

        # Setup target db with FK violation (short referencing nonexistent fact)
        shutil.copy2(self.source_db, self.target_db)
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("PRAGMA foreign_keys = OFF;")
        t_conn.execute("INSERT INTO shorts (fact_id, title, video_id) VALUES (9999, 'Orphan', 'vid_orphan');")
        t_conn.commit()
        t_conn.close()

        with self.assertRaises(RuntimeError) as ctx:
            restore_database(backup_file, self.target_db, is_offline_confirmed=True)
        self.assertIn("Pre-restore safety copy foreign key check found 1 violations!", str(ctx.exception))

    def test_failed_post_restore_verification_triggers_recovery(self):
        """
        Verify that if post-restore verification detects mismatch or integrity failure,
        the system automatically rolls back to the validated safety copy and reports
        explicit recovery status.
        """
        # Create an initial live target database with 3 facts
        shutil.copy2(self.source_db, self.target_db)
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("INSERT INTO facts (topic_title, narrative_text) VALUES ('Fact 3', 'Narrative 3');")
        t_conn.commit()
        t_conn.close()

        # Create a backup file from source (has 2 facts)
        backup_file = safe_online_backup(self.source_db, self.backup_dir)

        # Intercept os.replace to tamper with target_db after replacement, simulating a post-restore mismatch
        real_replace = os.replace
        tampered = {"done": False}

        def mock_replace(src, dst):
            real_replace(src, dst)
            if dst == self.target_db and not tampered["done"]:
                tampered["done"] = True
                # Mutate target_db so post-restore count check fails
                with sqlite3.connect(self.target_db) as mut_conn:
                    mut_conn.execute("DELETE FROM facts;")

        os.replace = mock_replace
        try:
            with self.assertRaises(RuntimeError) as ctx:
                restore_database(backup_file, self.target_db, is_offline_confirmed=True)

            err_msg = str(ctx.exception)
            self.assertIn("Post-restore verification failed", err_msg)
            self.assertIn("RECOVERY STATUS: SUCCESS", err_msg)
            self.assertIn("safely rolled back and restored from validated safety copy", err_msg)

        finally:
            os.replace = real_replace

        # Confirm target database was indeed rolled back to its pre-restore safety state (3 facts)
        rec_conn = sqlite3.connect(self.target_db)
        rec_cur = rec_conn.cursor()
        self.assertEqual(rec_cur.execute("PRAGMA integrity_check;").fetchone()[0], "ok")
        self.assertEqual(rec_cur.execute("SELECT count(*) FROM facts;").fetchone()[0], 3)
        rec_conn.close()


if __name__ == "__main__":
    unittest.main()
