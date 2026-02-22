import sys
import json
import os
from parser import extract_functions
from inference import client
from database import db


class AnalysisService:

    CPP_EXTENSIONS = ('.cpp', '.c', '.h', '.cc', '.cxx')

    def run_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        if not client.check_health():
            return {"error": "Kaggle API is unreachable. Make sure the notebook is running and the URL is set."}

        project_name = os.path.basename(file_path)
        analysis_id  = db.save_analysis(project_name, file_path)
        file_id      = db.save_file(analysis_id, file_path)

        functions = extract_functions(file_path)
        if not functions:
            return {"error": "No functions found in file. Is it a valid C++ file?"}

        results = []
        for fn in functions:
            result = client.analyze_function(fn["code"])
            if "error" in result:
                return {"error": result["error"]}
            full_fn = {**fn, **result}
            db.save_function(file_id, full_fn)
            results.append(full_fn)

        vuln_count = sum(1 for r in results if r["verdict"] == "vulnerable")
        return {
            "analysis_id":     analysis_id,
            "project_name":    project_name,
            "file_path":       file_path,
            "total_functions": len(results),
            "vuln_count":      vuln_count,
            "functions":       results,
        }

    def run_folder(self, folder_path: str) -> dict:
        if not os.path.exists(folder_path):
            return {"error": f"Folder not found: {folder_path}"}
        if not client.check_health():
            return {"error": "Kaggle API is unreachable. Make sure the notebook is running."}

        cpp_files = []
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')
                       and d not in ('build', 'cmake', 'node_modules')]
            for file in files:
                if file.endswith(self.CPP_EXTENSIONS):
                    cpp_files.append(os.path.join(root, file))

        if not cpp_files:
            return {"error": "No C++ files found in folder."}

        project_name = os.path.basename(folder_path.rstrip('/\\'))
        analysis_id  = db.save_analysis(project_name, folder_path)

        all_functions, total_vuln = [], 0

        for file_path in cpp_files:
            file_id   = db.save_file(analysis_id, file_path)
            functions = extract_functions(file_path)
            for fn in functions:
                result = client.analyze_function(fn["code"])
                if "error" in result:
                    return {"error": result["error"]}
                full_fn = {**fn, **result, "file_path": file_path}
                db.save_function(file_id, full_fn)
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


# Global singleton
service = AnalysisService()


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No file path provided"}))
            sys.exit(1)
        print(json.dumps(service.run_file(sys.argv[2]), indent=2))

    elif command == "analyze_folder":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No folder path provided"}))
            sys.exit(1)
        print(json.dumps(service.run_folder(sys.argv[2]), indent=2))

    elif command == "history":
        print(json.dumps(db.get_all_analyses(), indent=2))

    elif command == "report":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No analysis ID provided"}))
            sys.exit(1)
        report = db.get_report(int(sys.argv[2]))
        print(json.dumps(report if report else {"error": "Report not found"}, indent=2))

    elif command == "delete_analysis":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No analysis ID provided"}))
            sys.exit(1)
        db.delete_analysis(int(sys.argv[2]))
        print(json.dumps({"deleted": True}))

    elif command == "dashboard":
        print(json.dumps(db.get_dashboard_stats(), indent=2))

    elif command == "extract_functions":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "No file path provided"}))
            sys.exit(1)
        functions = extract_functions(sys.argv[2])
        print(json.dumps({"functions": functions, "count": len(functions)}))

    elif command == "check_api":
        print(json.dumps({"reachable": client.check_health()}))

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()