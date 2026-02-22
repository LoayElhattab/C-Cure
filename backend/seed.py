"""
Run this to seed the DB with fake analysis data for UI testing.
Usage: python seed.py
"""
from database import db

db.init_db()

# Create a fake analysis
aid = db.save_analysis("test_vulnerable.cpp", "C:/Users/test/Desktop/test_vulnerable.cpp")
fid = db.save_file(aid, "C:/Users/test/Desktop/test_vulnerable.cpp")

functions = [
    {
        "name": "readBuffer", "code": "void readBuffer(char* buf, int len) {\n    for (int i = 0; i <= len; i++) {\n        printf(\"%c\", buf[i]);\n    }\n}",
        "verdict": "vulnerable", "cwe": "CWE-125", "cwe_name": "Out-of-bounds Read",
        "severity": "High", "confidence": 0.91, "start_line": 6, "end_line": 10,
    },
    {
        "name": "copyData", "code": "void copyData(char* dst, char* src) {\n    strcpy(dst, src);\n}",
        "verdict": "vulnerable", "cwe": "CWE-787", "cwe_name": "Out-of-bounds Write",
        "severity": "Critical", "confidence": 0.88, "start_line": 13, "end_line": 15,
    },
    {
        "name": "calculateSize", "code": "int calculateSize(int a, int b) {\n    int result = a * b;\n    return result;\n}",
        "verdict": "vulnerable", "cwe": "CWE-190", "cwe_name": "Integer Overflow",
        "severity": "Medium", "confidence": 0.76, "start_line": 18, "end_line": 21,
    },
    {
        "name": "divide", "code": "float divide(float a, float b) {\n    return a / b;\n}",
        "verdict": "vulnerable", "cwe": "CWE-369", "cwe_name": "Divide By Zero",
        "severity": "Medium", "confidence": 0.83, "start_line": 24, "end_line": 26,
    },
    {
        "name": "processData", "code": "void processData(char* data) {\n    char* buf = (char*)malloc(100);\n    free(buf);\n    free(buf);\n}",
        "verdict": "vulnerable", "cwe": "CWE-415", "cwe_name": "Double Free",
        "severity": "High", "confidence": 0.95, "start_line": 29, "end_line": 33,
    },
    {
        "name": "getLength", "code": "int getLength(char* str) {\n    return strlen(str);\n}",
        "verdict": "vulnerable", "cwe": "CWE-476", "cwe_name": "NULL Pointer Dereference",
        "severity": "High", "confidence": 0.79, "start_line": 36, "end_line": 38,
    },
    {
        "name": "add", "code": "int add(int a, int b) {\n    return a + b;\n}",
        "verdict": "safe", "cwe": None, "cwe_name": None,
        "severity": None, "confidence": 0.97, "start_line": 41, "end_line": 43,
    },
    {
        "name": "printMessage", "code": "void printMessage(const char* msg) {\n    if (msg != nullptr) {\n        printf(\"%s\\n\", msg);\n    }\n}",
        "verdict": "safe", "cwe": None, "cwe_name": None,
        "severity": None, "confidence": 0.99, "start_line": 46, "end_line": 50,
    },
]

for fn in functions:
    db.save_function(fid, fn)

print(f"✓ Seeded analysis ID {aid} with {len(functions)} functions")
print(f"  Open the app and go to: /report/{aid}")