import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'ccure.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist yet."""
    conn = get_connection()
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
    """)
    conn.commit()
    conn.close()


def save_analysis(project_name: str, project_path: str) -> int:
    """Create a new analysis record. Returns the new analysis ID."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO analyses (project_name, project_path) VALUES (?, ?)",
        (project_name, project_path)
    )
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return analysis_id


def save_file(analysis_id: int, file_path: str) -> int:
    """Create a file record under an analysis. Returns the new file ID."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO files (analysis_id, file_path) VALUES (?, ?)",
        (analysis_id, file_path)
    )
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id


def save_function(file_id: int, fn: dict):
    """Save a single analyzed function result."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO functions
            (file_id, function_name, code, verdict, cwe, cwe_name, severity, confidence, start_line, end_line)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def get_all_analyses() -> list[dict]:
    """Fetch all analyses for the history page."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            a.id,
            a.project_name,
            a.project_path,
            a.timestamp,
            COUNT(f.id)                                      AS total_functions,
            SUM(CASE WHEN f.verdict = 'vulnerable' THEN 1 ELSE 0 END) AS vuln_count
        FROM analyses a
        LEFT JOIN files fi ON fi.analysis_id = a.id
        LEFT JOIN functions f ON f.file_id = fi.id
        GROUP BY a.id
        ORDER BY a.timestamp DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report(analysis_id: int) -> dict | None:
    """Fetch a full report for one analysis."""
    conn = get_connection()

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


if __name__ == "__main__":
    init_db()
    print(f"✓ Database initialized at {DB_PATH}")

    # Quick smoke test
    aid = save_analysis("test_project", "/path/to/test.cpp")
    fid = save_file(aid, "/path/to/test.cpp")
    save_function(fid, {
        "name": "readBuffer",
        "code": "void readBuffer() {}",
        "verdict": "vulnerable",
        "cwe": "CWE-125",
        "cwe_name": "Out-of-bounds Read",
        "severity": "High",
        "confidence": 0.92,
        "start_line": 4,
        "end_line": 8,
    })

    report = get_report(aid)
    print(f"✓ Saved and retrieved analysis ID {aid}")
    print(f"  Function: {report['files'][0]['functions'][0]['function_name']}")
    print(f"  Verdict:  {report['files'][0]['functions'][0]['verdict']}")
    print(f"  CWE:      {report['files'][0]['functions'][0]['cwe']}")