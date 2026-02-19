use std::path::PathBuf;
use std::process::Command;

// Find the backend directory relative to the app
fn backend_path() -> PathBuf {
    let mut path = std::env::current_dir().unwrap();
    path.push("backend");
    path
}

fn run_python(args: Vec<&str>) -> Result<String, String> {
    let backend = backend_path();

    let output = Command::new("python")
        .args(&args)
        .current_dir(&backend)
        .output()
        .map_err(|e| format!("Failed to launch Python: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn analyze_file(file_path: String) -> Result<String, String> {
    run_python(vec!["main.py", "analyze", &file_path])
}

#[tauri::command]
fn analyze_folder(folder_path: String) -> Result<String, String> {
    run_python(vec!["main.py", "analyze_folder", &folder_path])
}

#[tauri::command]
fn get_history() -> Result<String, String> {
    run_python(vec!["main.py", "history"])
}

#[tauri::command]
fn get_report(analysis_id: i32) -> Result<String, String> {
    let id = analysis_id.to_string();
    run_python(vec!["main.py", "report", &id])
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            analyze_file,
            analyze_folder,
            get_history,
            get_report
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application")
}
