#[link(name = "rstrtmgr")]
extern "C" {}

use duckdb::{params, Connection, Result};
use std::env;
use std::path::PathBuf;
use std::time::Instant;

const CWES: &[(&str, &str, &str)] = &[
    ("CWE-125", "Out-of-bounds Read", "High"),
    ("CWE-787", "Out-of-bounds Write", "Critical"),
    ("CWE-190", "Integer Overflow or Wraparound", "High"),
    ("CWE-369", "Divide By Zero", "Medium"),
    ("CWE-415", "Double Free", "High"),
    ("CWE-476", "NULL Pointer Dereference", "High"),
];

const VULN_TEMPLATES: &[(&str, &str)] = &[
    (
        "CWE-787",
        "void copy_buffer(const char* src, size_t len) {\n    char dest[64];\n    // UNSAFE: No length check\n    strcpy(dest, src);\n}"
    ),
    (
        "CWE-125",
        "int read_from_index(const int* array, size_t size, int index) {\n    // UNSAFE: Array index not validated\n    return array[index];\n}"
    ),
    (
        "CWE-190",
        "void* allocate_buffer(int count) {\n    // UNSAFE: Integer multiplication overflow check missing\n    size_t total = count * sizeof(double);\n    return malloc(total);\n}"
    ),
    (
        "CWE-369",
        "double compute_average(double sum, int count) {\n    // UNSAFE: Count not checked for zero before division\n    return sum / count;\n}"
    ),
    (
        "CWE-415",
        "void free_resources(char* ptr) {\n    free(ptr);\n    // ... complex logic ...\n    // UNSAFE: Double free of the same pointer\n    free(ptr);\n}"
    ),
    (
        "CWE-476",
        "const char* get_username(struct User* user) {\n    // UNSAFE: NULL check missing on struct pointer\n    return user->username;\n}"
    ),
];

const SAFE_TEMPLATES: &[&str] = &[
    "int sum_array(const int* array, size_t size) {\n    int sum = 0;\n    for (size_t i = 0; i < size; ++i) {\n        sum += array[i];\n    }\n    return sum;\n}",
    "void print_status(int status_code) {\n    switch (status_code) {\n        case 200: printf(\"OK\\n\"); break;\n        case 404: printf(\"Not Found\\n\"); break;\n        default: printf(\"Unknown Code: %d\\n\", status_code); break;\n    }\n}",
    "bool is_valid_age(int age) {\n    return age >= 0 && age <= 150;\n}",
    "std::string make_greeting(const std::string& name) {\n    if (name.empty()) {\n        return \"Hello, Guest!\";\n    }\n    return \"Hello, \" + name + \"!\";\n}",
    "void cleanup_safe(char** ptr) {\n    if (ptr && *ptr) {\n        free(*ptr);\n        *ptr = nullptr;\n    }\n}",
    "int safe_divide(int dividend, int divisor) {\n    if (divisor == 0) {\n        return 0; // Prevent divide-by-zero\n    }\n    return dividend / divisor;\n}",
];

fn print_help() {
    println!(
        "CCure DuckDB Database Seeding Utility\n\n\
        Usage: cargo run --bin generate_gigantic_report [OPTIONS]\n\n\
        Options:\n  \
          --db <PATH>                  Path to the DuckDB database file\n  \
          --files <COUNT>              Number of files to generate (default: 1000)\n  \
          --functions-per-file <COUNT> Number of functions per file (default: 50)\n  \
          --vuln-rate <RATE>           Fraction of functions that are vulnerable (0.0 to 1.0, default: 0.10)\n  \
          --project-name <NAME>        Name of the project (default: GIGANTIC_TEST_PROJECT)\n  \
          --help, -h                   Show this help message\n"
    );
}

fn get_default_db_path() -> PathBuf {
    // 1. Try local AppData: AppData\Local\fcis\ccure.db
    if let Some(local_dir) = dirs::data_local_dir() {
        let p = local_dir.join("fcis").join("ccure.db");
        if p.exists() {
            return p;
        }
    }
    // 2. Try AppData/Roaming: AppData\Roaming\fcis\ccure.db
    if let Some(roaming_dir) = dirs::data_dir() {
        let p = roaming_dir.join("fcis").join("ccure.db");
        if p.exists() {
            return p;
        }
    }
    // 3. Check current folder
    let p = PathBuf::from("ccure.db");
    if p.exists() {
        return p;
    }
    // Default fallback path in Local AppData
    if let Some(local_dir) = dirs::data_local_dir() {
        local_dir.join("fcis").join("ccure.db")
    } else {
        PathBuf::from("ccure.db")
    }
}

fn init_db_on_conn(conn: &Connection) -> Result<()> {
    conn.execute_batch(
        "
        CREATE SEQUENCE IF NOT EXISTS seq_analyses START 1;
        CREATE SEQUENCE IF NOT EXISTS seq_files START 1;
        CREATE SEQUENCE IF NOT EXISTS seq_functions START 1;
        CREATE SEQUENCE IF NOT EXISTS seq_watched_projects START 1;
        CREATE SEQUENCE IF NOT EXISTS seq_file_hashes START 1;

        CREATE TABLE IF NOT EXISTS analyses (
            id           INTEGER PRIMARY KEY DEFAULT nextval('seq_analyses'),
            timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_name VARCHAR NOT NULL,
            project_path VARCHAR
        );
        CREATE TABLE IF NOT EXISTS files (
            id          INTEGER PRIMARY KEY DEFAULT nextval('seq_files'),
            analysis_id INTEGER NOT NULL,
            file_path   VARCHAR NOT NULL,
            FOREIGN KEY(analysis_id) REFERENCES analyses(id)
        );
        CREATE TABLE IF NOT EXISTS functions (
            id            INTEGER PRIMARY KEY DEFAULT nextval('seq_functions'),
            file_id       INTEGER NOT NULL,
            function_name VARCHAR NOT NULL,
            code          VARCHAR NOT NULL,
            verdict       VARCHAR NOT NULL,
            cwe           VARCHAR,
            cwe_name      VARCHAR,
            severity      VARCHAR,
            confidence    DOUBLE,
            start_line    INTEGER,
            end_line      INTEGER,
            FOREIGN KEY(file_id) REFERENCES files(id)
        );
        CREATE TABLE IF NOT EXISTS watched_projects (
            id            INTEGER PRIMARY KEY DEFAULT nextval('seq_watched_projects'),
            name          VARCHAR NOT NULL,
            folder_path   VARCHAR NOT NULL UNIQUE,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS file_hashes (
            id         INTEGER PRIMARY KEY DEFAULT nextval('seq_file_hashes'),
            project_id INTEGER NOT NULL,
            file_path  VARCHAR NOT NULL,
            file_hash  VARCHAR NOT NULL,
            hashed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, file_path),
            FOREIGN KEY(project_id) REFERENCES watched_projects(id)
        );

        CREATE INDEX IF NOT EXISTS idx_files_analysis_id ON files(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions(file_id);
        CREATE INDEX IF NOT EXISTS idx_functions_verdict ON functions(verdict);
        CREATE INDEX IF NOT EXISTS idx_functions_file_verdict ON functions(file_id, verdict);
        CREATE INDEX IF NOT EXISTS idx_file_hashes_project ON file_hashes(project_id);
        ",
    )?;
    Ok(())
}

fn main() -> std::result::Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();

    let mut db_path: Option<PathBuf> = None;
    let mut files_count = 1000;
    let mut functions_per_file = 50;
    let mut vuln_rate = 0.10;
    let mut project_name = "GIGANTIC_TEST_PROJECT".to_string();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--db" => {
                if i + 1 < args.len() {
                    db_path = Some(PathBuf::from(&args[i + 1]));
                    i += 2;
                } else {
                    return Err("Missing value for --db".into());
                }
            }
            "--files" => {
                if i + 1 < args.len() {
                    files_count = args[i + 1].parse()?;
                    i += 2;
                } else {
                    return Err("Missing value for --files".into());
                }
            }
            "--functions-per-file" => {
                if i + 1 < args.len() {
                    functions_per_file = args[i + 1].parse()?;
                    i += 2;
                } else {
                    return Err("Missing value for --functions-per-file".into());
                }
            }
            "--vuln-rate" => {
                if i + 1 < args.len() {
                    vuln_rate = args[i + 1].parse()?;
                    i += 2;
                } else {
                    return Err("Missing value for --vuln-rate".into());
                }
            }
            "--project-name" => {
                if i + 1 < args.len() {
                    project_name = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err("Missing value for --project-name".into());
                }
            }
            "--help" | "-h" => {
                print_help();
                return Ok(());
            }
            _ => {
                println!("Unknown argument: {}", args[i]);
                print_help();
                return Err("Invalid arguments".into());
            }
        }
    }

    let resolved_db_path = db_path.unwrap_or_else(get_default_db_path);
    println!("Target Database Path: {:?}", resolved_db_path);

    // Ensure parent directories exist
    if let Some(parent) = resolved_db_path.parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent)?;
        }
    }

    let start_time = Instant::now();
    println!("Connecting to DuckDB...");
    let mut conn = Connection::open(&resolved_db_path)?;

    println!("Initializing tables...");
    init_db_on_conn(&conn)?;

    println!("Starting database transaction...");
    let tx = conn.transaction()?;

    // Insert analysis
    println!("Seeding analysis meta info...");
    let project_path = format!("/mock/projects/{}", project_name);
    let mut stmt = tx.prepare(
        "INSERT INTO analyses (project_name, project_path, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP) RETURNING id"
    )?;
    let analysis_id: i64 = stmt.query_row(params![project_name, project_path], |row| row.get(0))?;
    drop(stmt);
    println!("Generated Analysis ID: {}", analysis_id);

    println!("Preparing bulk insertions for files and functions...");
    let total_functions = files_count * functions_per_file;
    println!(
        "Plan: Generate {} files containing {} functions each (Total: {} functions)",
        files_count, functions_per_file, total_functions
    );

    // Prepare insert statement for files to get their generated IDs
    let mut file_stmt =
        tx.prepare("INSERT INTO files (analysis_id, file_path) VALUES (?, ?) RETURNING id")?;

    // Create Appender for functions
    let mut appender = tx.appender("functions")?;
    appender.add_column("file_id")?;
    appender.add_column("function_name")?;
    appender.add_column("code")?;
    appender.add_column("verdict")?;
    appender.add_column("cwe")?;
    appender.add_column("cwe_name")?;
    appender.add_column("severity")?;
    appender.add_column("confidence")?;
    appender.add_column("start_line")?;
    appender.add_column("end_line")?;

    let mut seeded_vulnerable = 0;
    let mut seeded_safe = 0;

    let vuln_templates_count = VULN_TEMPLATES.len();
    let safe_templates_count = SAFE_TEMPLATES.len();

    let mut report_interval = files_count / 10;
    if report_interval == 0 {
        report_interval = 1;
    }

    for f_idx in 1..=files_count {
        let file_path = format!(
            "src/components/module_{:04}/component_{:04}.cpp",
            f_idx / 10,
            f_idx
        );

        // Insert file and get its ID
        let file_id: i64 =
            file_stmt.query_row(params![analysis_id, file_path], |row| row.get(0))?;

        for fn_idx in 1..=functions_per_file {
            let func_index = (f_idx - 1) * functions_per_file + fn_idx;

            // Simple pseudo-randomness based on index (so we don't need rand dependency)
            let is_vulnerable = ((func_index * 17 + 5) % 100) < (vuln_rate * 100.0) as usize;

            let function_name = if is_vulnerable {
                format!("process_input_vulnerable_{}", func_index)
            } else {
                format!("calculate_metrics_safe_{}", func_index)
            };

            let start_line = (fn_idx * 15) as i32;
            let end_line = start_line + 10;
            let confidence = if is_vulnerable {
                0.70 + (((func_index * 3) % 25) as f64) / 100.0 // 0.70 to 0.94
            } else {
                0.85 + (((func_index * 7) % 15) as f64) / 100.0 // 0.85 to 0.99
            };

            if is_vulnerable {
                // Select a template/CWE
                let t_idx = func_index % vuln_templates_count;
                let (cwe, code) = VULN_TEMPLATES[t_idx];

                // Get CWE details
                let mut cwe_name = "Unknown Weakness";
                let mut severity = "Medium";
                for &(c, cn, sev) in CWES {
                    if c == cwe {
                        cwe_name = cn;
                        severity = sev;
                        break;
                    }
                }

                appender.append_row(params![
                    file_id,
                    function_name,
                    code,
                    "vulnerable",
                    Some(cwe.to_string()),
                    Some(cwe_name.to_string()),
                    Some(severity.to_string()),
                    Some(confidence),
                    Some(start_line),
                    Some(end_line),
                ])?;
                seeded_vulnerable += 1;
            } else {
                // Select safe template
                let t_idx = func_index % safe_templates_count;
                let code = SAFE_TEMPLATES[t_idx];

                appender.append_row(params![
                    file_id,
                    function_name,
                    code,
                    "safe",
                    None::<String>,
                    None::<String>,
                    None::<String>,
                    Some(confidence),
                    Some(start_line),
                    Some(end_line),
                ])?;
                seeded_safe += 1;
            }
        }

        if f_idx % report_interval == 0 || f_idx == files_count {
            let elapsed = start_time.elapsed();
            println!(
                "Progress: {}/{} files generated ({:.1}%). Elapsed time: {:.2?}",
                f_idx,
                files_count,
                (f_idx as f64 / files_count as f64) * 100.0,
                elapsed
            );
        }
    }

    println!("Flushing Appender...");
    appender.flush()?;
    drop(appender);
    drop(file_stmt);

    println!("Committing transaction to database...");
    tx.commit()?;

    let total_elapsed = start_time.elapsed();
    println!("\nSeeding Completed Successfully!");
    println!("--------------------------------");
    println!("Database Path:       {:?}", resolved_db_path);
    println!("Analysis ID:         {}", analysis_id);
    println!("Files Generated:     {}", files_count);
    println!("Safe Functions:      {}", seeded_safe);
    println!("Vulnerable Functions: {}", seeded_vulnerable);
    println!("Total Functions:     {}", seeded_safe + seeded_vulnerable);
    println!("Execution Time:      {:.2?}", total_elapsed);
    println!(
        "Avg Insert Rate:     {:.0} functions/sec",
        (total_functions as f64) / total_elapsed.as_secs_f64()
    );

    Ok(())
}
