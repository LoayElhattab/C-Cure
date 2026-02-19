import os
import sys
import json
import sqlite3
import unittest
import tempfile

# Make sure imports resolve
sys.path.insert(0, os.path.dirname(__file__))

from parser import extract_functions
from database import (
    init_db, save_analysis, save_file, save_function,
    get_all_analyses, get_report, DB_PATH
)
import main as m


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_temp_cpp(code: str) -> str:
    """Write a temp .cpp file and return its path."""
    f = tempfile.NamedTemporaryFile(suffix='.cpp', delete=False, mode='w')
    f.write(code)
    f.close()
    return f.name


def wipe_db():
    """Clear all tables between tests."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DELETE FROM functions;
        DELETE FROM files;
        DELETE FROM analyses;
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Parser Tests
# ─────────────────────────────────────────────

class TestParser(unittest.TestCase):

    def test_extracts_basic_function(self):
        path = make_temp_cpp("""
void hello() {
    printf("hello");
}
""")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(len(fns), 1)
        self.assertEqual(fns[0]['name'], 'hello')

    def test_extracts_multiple_functions(self):
        path = make_temp_cpp("""
void foo() {}
int bar(int x) { return x; }
bool baz(char* s) { return s != nullptr; }
""")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(len(fns), 3)
        names = [f['name'] for f in fns]
        self.assertIn('foo', names)
        self.assertIn('bar', names)
        self.assertIn('baz', names)

    def test_extracts_template_function(self):
        path = make_temp_cpp("""
template<typename T>
T safeDivide(T a, T b) {
    if (b == 0) return 0;
    return a / b;
}
""")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(len(fns), 1)
        self.assertEqual(fns[0]['name'], 'safeDivide')

    def test_returns_correct_line_numbers(self):
        path = make_temp_cpp("""void foo() {
    int x = 1;
}

void bar() {
    int y = 2;
}
""")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(fns[0]['start_line'], 1)
        self.assertEqual(fns[1]['start_line'], 5)

    def test_empty_file_returns_empty_list(self):
        path = make_temp_cpp("")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(fns, [])

    def test_file_with_only_comments(self):
        path = make_temp_cpp("// just a comment\n/* nothing here */\n")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertEqual(fns, [])

    def test_nonexistent_file_returns_empty(self):
        fns = extract_functions("/nonexistent/path/file.cpp")
        self.assertEqual(fns, [])

    def test_code_snippet_is_correct(self):
        path = make_temp_cpp("void greet() {\n    printf(\"hi\");\n}\n")
        fns = extract_functions(path)
        os.unlink(path)
        self.assertIn('greet', fns[0]['code'])
        self.assertIn('printf', fns[0]['code'])


# ─────────────────────────────────────────────
# Database Tests
# ─────────────────────────────────────────────

class TestDatabase(unittest.TestCase):

    def setUp(self):
        init_db()
        wipe_db()

    def test_save_and_fetch_analysis(self):
        aid = save_analysis("test.cpp", "/path/test.cpp")
        self.assertIsInstance(aid, int)
        self.assertGreater(aid, 0)

    def test_save_file_under_analysis(self):
        aid = save_analysis("test.cpp", "/path/test.cpp")
        fid = save_file(aid, "/path/test.cpp")
        self.assertIsInstance(fid, int)
        self.assertGreater(fid, 0)

    def test_save_vulnerable_function(self):
        aid = save_analysis("test.cpp", "/path/test.cpp")
        fid = save_file(aid, "/path/test.cpp")
        save_function(fid, {
            "name": "readBuffer",
            "code": "void readBuffer() {}",
            "verdict": "vulnerable",
            "cwe": "CWE-125",
            "cwe_name": "Out-of-bounds Read",
            "severity": "High",
            "confidence": 0.92,
            "start_line": 1,
            "end_line": 3,
        })
        report = get_report(aid)
        fn = report['files'][0]['functions'][0]
        self.assertEqual(fn['verdict'], 'vulnerable')
        self.assertEqual(fn['cwe'], 'CWE-125')
        self.assertAlmostEqual(fn['confidence'], 0.92)

    def test_save_safe_function(self):
        aid = save_analysis("test.cpp", "/path/test.cpp")
        fid = save_file(aid, "/path/test.cpp")
        save_function(fid, {
            "name": "cleanup",
            "code": "void cleanup() {}",
            "verdict": "safe",
            "cwe": None,
            "cwe_name": None,
            "severity": None,
            "confidence": None,
            "start_line": 1,
            "end_line": 1,
        })
        report = get_report(aid)
        fn = report['files'][0]['functions'][0]
        self.assertEqual(fn['verdict'], 'safe')
        self.assertIsNone(fn['cwe'])

    def test_get_all_analyses_returns_list(self):
        save_analysis("a.cpp", "/a.cpp")
        save_analysis("b.cpp", "/b.cpp")
        history = get_all_analyses()
        self.assertGreaterEqual(len(history), 2)

    def test_history_counts_are_correct(self):
        aid = save_analysis("test.cpp", "/test.cpp")
        fid = save_file(aid, "/test.cpp")
        save_function(fid, {"name": "f1", "code": "", "verdict": "vulnerable",
                            "cwe": "CWE-125", "cwe_name": "OOB", "severity": "High",
                            "confidence": 0.9, "start_line": 1, "end_line": 2})
        save_function(fid, {"name": "f2", "code": "", "verdict": "safe",
                            "cwe": None, "cwe_name": None, "severity": None,
                            "confidence": None, "start_line": 3, "end_line": 4})
        history = get_all_analyses()
        entry = next(h for h in history if h['id'] == aid)
        self.assertEqual(entry['total_functions'], 2)
        self.assertEqual(entry['vuln_count'], 1)

    def test_get_report_invalid_id_returns_none(self):
        report = get_report(99999)
        self.assertIsNone(report)

    def test_cascade_delete(self):
        """Deleting an analysis should wipe its files and functions."""
        aid = save_analysis("test.cpp", "/test.cpp")
        fid = save_file(aid, "/test.cpp")
        save_function(fid, {"name": "fn", "code": "", "verdict": "safe",
                            "cwe": None, "cwe_name": None, "severity": None,
                            "confidence": None, "start_line": 1, "end_line": 1})
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM analyses WHERE id = ?", (aid,))
        conn.commit()
        fns = conn.execute("SELECT * FROM functions WHERE file_id = ?", (fid,)).fetchall()
        conn.close()
        self.assertEqual(len(fns), 0)


# ─────────────────────────────────────────────
# Main / Pipeline Tests (no API needed)
# ─────────────────────────────────────────────

class TestMain(unittest.TestCase):

    def setUp(self):
        init_db()
        wipe_db()

    def test_run_analysis_missing_file(self):
        result = m.run_analysis("/nonexistent/file.cpp")
        self.assertIn("error", result)

    def test_fetch_report_invalid_id(self):
        result = m.fetch_report(99999)
        self.assertIn("error", result)

    def test_fetch_history_returns_list(self):
        result = m.fetch_history()
        self.assertIsInstance(result, list)

    def test_history_reflects_saved_data(self):
        aid = save_analysis("demo.cpp", "/demo.cpp")
        history = m.fetch_history()
        ids = [h['id'] for h in history]
        self.assertIn(aid, ids)

    def test_fetch_report_returns_correct_structure(self):
        aid = save_analysis("demo.cpp", "/demo.cpp")
        fid = save_file(aid, "/demo.cpp")
        save_function(fid, {"name": "foo", "code": "void foo(){}", "verdict": "safe",
                            "cwe": None, "cwe_name": None, "severity": None,
                            "confidence": None, "start_line": 1, "end_line": 1})
        report = m.fetch_report(aid)
        self.assertIn("files", report)
        self.assertIn("project_name", report)
        self.assertEqual(report["project_name"], "demo.cpp")
        self.assertEqual(len(report["files"][0]["functions"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)