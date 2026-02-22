import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'ccure.db')


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS analyses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
                project_name TEXT NOT NULL,
                project_path TEXT
            );
            CREATE TABLE IF NOT EXISTS files (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                file_path   TEXT NOT NULL,
                FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS functions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id       INTEGER NOT NULL,
                function_name TEXT NOT NULL,
                code          TEXT NOT NULL,
                verdict       TEXT NOT NULL,
                cwe           TEXT,
                cwe_name      TEXT,
                severity      TEXT,
                confidence    REAL,
                start_line    INTEGER,
                end_line      INTEGER,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS watched_projects (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                folder_path   TEXT NOT NULL UNIQUE,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS file_hashes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                file_path  TEXT NOT NULL,
                file_hash  TEXT NOT NULL,
                hashed_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, file_path),
                FOREIGN KEY(project_id) REFERENCES watched_projects(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        conn.close()

    # ── Analyses ──────────────────────────────────────────

    def save_analysis(self, project_name: str, project_path: str) -> int:
        conn = self.get_connection()
        cursor = conn.execute(
            "INSERT INTO analyses (project_name, project_path) VALUES (?, ?)",
            (project_name, project_path)
        )
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return analysis_id

    def delete_analysis(self, analysis_id: int):
        conn = self.get_connection()
        conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()

    def get_all_analyses(self) -> list[dict]:
        conn = self.get_connection()
        rows = conn.execute("""
            SELECT
                a.id, a.project_name, a.project_path, a.timestamp,
                COUNT(f.id) AS total_functions,
                SUM(CASE WHEN f.verdict = 'vulnerable' THEN 1 ELSE 0 END) AS vuln_count
            FROM analyses a
            LEFT JOIN files fi ON fi.analysis_id = a.id
            LEFT JOIN functions f ON f.file_id = fi.id
            GROUP BY a.id
            ORDER BY a.timestamp DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_report(self, analysis_id: int) -> dict | None:
        conn = self.get_connection()
        analysis = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        if not analysis:
            conn.close()
            return None
        files = conn.execute(
            "SELECT * FROM files WHERE analysis_id = ?", (analysis_id,)
        ).fetchall()
        result = {
            "id": analysis["id"],
            "project_name": analysis["project_name"],
            "project_path": analysis["project_path"],
            "timestamp": analysis["timestamp"],
            "files": []
        }
        for file in files:
            functions = conn.execute(
                "SELECT * FROM functions WHERE file_id = ?", (file["id"],)
            ).fetchall()
            result["files"].append({
                "file_path": file["file_path"],
                "functions": [dict(f) for f in functions]
            })
        conn.close()
        return result

    # ── Files & Functions ─────────────────────────────────

    def save_file(self, analysis_id: int, file_path: str) -> int:
        conn = self.get_connection()
        cursor = conn.execute(
            "INSERT INTO files (analysis_id, file_path) VALUES (?, ?)",
            (analysis_id, file_path)
        )
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id

    def save_function(self, file_id: int, fn: dict):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO functions
                (file_id, function_name, code, verdict, cwe, cwe_name,
                 severity, confidence, start_line, end_line)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            fn.get('name'),
            fn.get('code'),
            fn.get('verdict'),
            fn.get('cwe'),
            fn.get('cwe_name'),
            fn.get('severity'),
            fn.get('confidence'),
            fn.get('start_line'),
            fn.get('end_line'),
        ))
        conn.commit()
        conn.close()

    # ── Dashboard ─────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        conn = self.get_connection()

        kpis = conn.execute("""
            SELECT
                COUNT(DISTINCT a.id)                                       AS total_analyses,
                COUNT(DISTINCT fi.id)                                      AS total_files,
                COUNT(f.id)                                                AS total_functions,
                SUM(CASE WHEN f.verdict = 'vulnerable' THEN 1 ELSE 0 END) AS total_vulnerable,
                SUM(CASE WHEN f.verdict = 'safe'       THEN 1 ELSE 0 END) AS total_safe
            FROM analyses a
            LEFT JOIN files fi ON fi.analysis_id = a.id
            LEFT JOIN functions f ON f.file_id = fi.id
        """).fetchone()

        cwe_counts = conn.execute("""
            SELECT cwe, cwe_name, severity, COUNT(*) AS count
            FROM functions
            WHERE verdict = 'vulnerable' AND cwe IS NOT NULL
            GROUP BY cwe ORDER BY count DESC
        """).fetchall()

        severity_counts = conn.execute("""
            SELECT severity, COUNT(*) AS count
            FROM functions
            WHERE verdict = 'vulnerable' AND severity IS NOT NULL
            GROUP BY severity
        """).fetchall()

        file_ratios = conn.execute("""
            SELECT
                fi.file_path,
                SUM(CASE WHEN f.verdict = 'safe'       THEN 1 ELSE 0 END) AS safe_count,
                SUM(CASE WHEN f.verdict = 'vulnerable' THEN 1 ELSE 0 END) AS vuln_count
            FROM files fi
            JOIN functions f ON f.file_id = fi.id
            GROUP BY fi.id ORDER BY fi.id DESC LIMIT 10
        """).fetchall()

        confidence_bins = conn.execute("""
            SELECT
                SUM(CASE WHEN confidence < 0.5                       THEN 1 ELSE 0 END) AS bin_0_50,
                SUM(CASE WHEN confidence >= 0.5 AND confidence < 0.7 THEN 1 ELSE 0 END) AS bin_50_70,
                SUM(CASE WHEN confidence >= 0.7 AND confidence < 0.9 THEN 1 ELSE 0 END) AS bin_70_90,
                SUM(CASE WHEN confidence >= 0.9                      THEN 1 ELSE 0 END) AS bin_90_100
            FROM functions WHERE confidence IS NOT NULL
        """).fetchone()

        recent = conn.execute("""
            SELECT
                a.id, a.project_name, a.timestamp,
                COUNT(f.id)                                                AS total_functions,
                SUM(CASE WHEN f.verdict = 'vulnerable' THEN 1 ELSE 0 END) AS vuln_count
            FROM analyses a
            LEFT JOIN files fi ON fi.analysis_id = a.id
            LEFT JOIN functions f ON f.file_id = fi.id
            GROUP BY a.id ORDER BY a.timestamp DESC LIMIT 7
        """).fetchall()

        conn.close()

        return {
            "kpis": dict(kpis),
            "cwe_counts": [dict(r) for r in cwe_counts],
            "severity_counts": [dict(r) for r in severity_counts],
            "file_ratios": [
                {
                    "label": r["file_path"].replace("\\", "/").split("/")[-1],
                    "safe":  r["safe_count"],
                    "vuln":  r["vuln_count"],
                }
                for r in file_ratios
            ],
            "confidence_bins": dict(confidence_bins) if confidence_bins else {},
            "recent_analyses": [dict(r) for r in recent],
        }

    # ── Monitor ───────────────────────────────────────────

    def add_watched_project(self, name: str, folder_path: str) -> dict:
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO watched_projects (name, folder_path) VALUES (?, ?)",
                (name, folder_path)
            )
            project_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {"id": project_id, "name": name, "folder_path": folder_path}
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": "This folder is already being watched."}

    def get_watched_projects(self) -> list[dict]:
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT * FROM watched_projects ORDER BY registered_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_file_hashes(self, project_id: int, hashes: dict):
        conn = self.get_connection()
        for file_path, file_hash in hashes.items():
            conn.execute("""
                INSERT INTO file_hashes (project_id, file_path, file_hash)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id, file_path)
                DO UPDATE SET file_hash = excluded.file_hash,
                              hashed_at = CURRENT_TIMESTAMP
            """, (project_id, file_path, file_hash))
        conn.commit()
        conn.close()

    def get_file_hashes(self, project_id: int) -> dict:
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT file_path, file_hash FROM file_hashes WHERE project_id = ?",
            (project_id,)
        ).fetchall()
        conn.close()
        return {r["file_path"]: r["file_hash"] for r in rows}

    def remove_watched_project(self, project_id: int):
        conn = self.get_connection()
        conn.execute("DELETE FROM watched_projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()


# Global singleton — imported everywhere
db = DatabaseManager()