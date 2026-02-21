import sys
import json
import os
from parser import extract_functions
from inference import analyze_function, check_api_health
from database import init_db, save_analysis, save_file, save_function, get_all_analyses, get_report, get_dashboard_stats

# Initialize DB on every startup — safe to call multiple times
init_db()


def run_analysis(file_path: str) -> dict:
    """
    Full pipeline for a single .cpp file.
    Returns a complete report dict.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    if not check_api_health():
        return {"error": "Kaggle API is unreachable. Make sure the notebook is running and the URL is set."}

    project_name = os.path.basename(file_path)

    # 1. Save analysis record
    analysis_id = save_analysis(project_name, file_path)
    file_id = save_file(analysis_id, file_path)

    # 2. Extract functions
    functions = extract_functions(file_path)
    if not functions:
        return {"error": "No functions found in file. Is it a valid C++ file?"}

    # 3. Run inference on each function
    results = []
    for fn in functions:
        inference_result = analyze_function(fn["code"])

        if "error" in inference_result:
            return {"error": inference_result["error"]}

        full_fn = {
            "name":       fn["name"],
            "code":       fn["code"],
            "start_line": fn["start_line"],
            "end_line":   fn["end_line"],
            **inference_result
        }

        save_function(file_id, full_fn)
        results.append(full_fn)

    # 4. Build summary
    vuln_count = sum(1 for r in results if r["verdict"] == "vulnerable")

    return {
        "analysis_id":    analysis_id,
        "project_name":   project_name,
        "file_path":      file_path,
        "total_functions": len(results),
        "vuln_count":     vuln_count,
        "functions":      results,
    }


def fetch_history() -> list:
    return get_all_analyses()


def fetch_report(analysis_id: int) -> dict:
    report = get_report(analysis_id)
    if not report:
        return {"error": f"No report found for analysis ID {analysis_id}"}
    return report

def fetch_dashboard() -> dict:
    return get_dashboard_stats()

def run_analysis_folder(folder_path: str) -> dict:
    """
    Full pipeline for an entire project folder.
    Finds all .cpp/.c/.h files and runs them through the pipeline.
    """
    if not os.path.exists(folder_path):
        return {"error": f"Folder not found: {folder_path}"}

    if not check_api_health():
        return {"error": "Kaggle API is unreachable. Make sure the notebook is running."}

    # Find all C++ files recursively
    cpp_extensions = ('.cpp', '.c', '.h', '.cc', '.cxx')
    cpp_files = []
    for root, dirs, files in os.walk(folder_path):
        # Skip hidden folders and build artifacts
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('build', 'cmake', 'node_modules')]
        for file in files:
            if file.endswith(cpp_extensions):
                cpp_files.append(os.path.join(root, file))

    if not cpp_files:
        return {"error": "No C++ files found in folder."}

    project_name = os.path.basename(folder_path.rstrip('/\\'))
    analysis_id = save_analysis(project_name, folder_path)

    all_functions = []
    total_vuln = 0

    for file_path in cpp_files:
        file_id = save_file(analysis_id, file_path)
        functions = extract_functions(file_path)

        for fn in functions:
            inference_result = analyze_function(fn["code"])

            if "error" in inference_result:
                return {"error": inference_result["error"]}

            full_fn = {
                "name":       fn["name"],
                "code":       fn["code"],
                "start_line": fn["start_line"],
                "end_line":   fn["end_line"],
                "file_path":  file_path,
                **inference_result
            }

            save_function(file_id, full_fn)
            all_functions.append(full_fn)

            if full_fn["verdict"] == "vulnerable":
                total_vuln += 1

    return {
        "analysis_id":     analysis_id,
        "project_name":    project_name,
        "folder_path":     folder_path,
        "files_scanned":   len(cpp_files),
        "total_functions": len(all_functions),
        "vuln_count":      total_vuln,
        "functions":       all_functions,
    }


def main():
    """
    CLI entry point — Tauri calls this via subprocess.
    Usage:
      python main.py analyze <file_path>
      python main.py history
      python main.py report <analysis_id>
    """
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No file path provided"}))
            sys.exit(1)
        result = run_analysis(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif command == "history":
        result = fetch_history()
        print(json.dumps(result, indent=2))

    elif command == "report":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No analysis ID provided"}))
            sys.exit(1)
        result = fetch_report(int(sys.argv[2]))
        print(json.dumps(result, indent=2))

    elif command == "analyze_folder":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No folder path provided"}))
            sys.exit(1)
        result = run_analysis_folder(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif command == "dashboard":
        result = fetch_dashboard()
        print(json.dumps(result, indent=2))

    elif command == "extract_functions":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No file path provided"}))
            sys.exit(1)
        from parser import extract_functions
        functions = extract_functions(sys.argv[2])
        print(json.dumps({"functions": functions, "count": len(functions)}))

    elif command == "check_api":
        from inference import check_api_health
        ok = check_api_health()
        print(json.dumps({"reachable": ok}))

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()