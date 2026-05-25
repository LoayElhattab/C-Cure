use duckdb::params;
use std::collections::HashMap;

use crate::db::{DbPool, WatchedProject};
use crate::error::AppError;

fn is_unique_violation(err: &duckdb::Error) -> bool {
    let msg = err.to_string().to_lowercase();
    msg.contains("unique")
        || msg.contains("constraint")
        || msg.contains("duplicate")
        || msg.contains("primary key")
}

pub async fn add_watched_project(
    pool: &DbPool,
    name: String,
    folder_path: String,
) -> Result<i32, AppError> {
    pool.with_conn(move |conn| {
        match conn.execute(
            "INSERT INTO watched_projects (name, folder_path) VALUES (?, ?)",
            params![name, folder_path],
        ) {
            Ok(_) => {
                let mut stmt = conn.prepare("SELECT last_insert_rowid()")?;
                let id: i64 = stmt.query_row([], |row| row.get(0))?;
                Ok(id as i32)
            }
            Err(e) if is_unique_violation(&e) => {
                Err(duckdb::Error::InvalidParameterName("Constraint".into()))
            }
            Err(e) => Err(e),
        }
    })
    .await
}

pub async fn get_watched_projects(pool: &DbPool) -> Result<Vec<WatchedProject>, AppError> {
    pool.with_conn(|conn| {
        let mut stmt = conn.prepare(
            "SELECT id, name, folder_path, CAST(registered_at AS VARCHAR)
             FROM watched_projects ORDER BY registered_at DESC",
        )?;
        let iter = stmt.query_map([], |row| {
            Ok(WatchedProject {
                id: row.get(0)?,
                name: row.get(1)?,
                folder_path: row.get(2)?,
                registered_at: row.get(3)?,
            })
        })?;
        let mut projects = Vec::new();
        for r in iter {
            projects.push(r?);
        }
        Ok(projects)
    })
    .await
}

pub async fn save_file_hashes(
    pool: &DbPool,
    project_id: i32,
    hashes: HashMap<String, String>,
) -> Result<(), AppError> {
    pool.with_conn(move |conn| {
        let mut stmt = conn.prepare(
            "INSERT INTO file_hashes (project_id, file_path, file_hash)
             VALUES (?, ?, ?)
             ON CONFLICT (project_id, file_path)
             DO UPDATE SET file_hash = EXCLUDED.file_hash, hashed_at = CURRENT_TIMESTAMP",
        )?;
        for (path, hash) in &hashes {
            stmt.execute(params![project_id, path, hash])?;
        }
        Ok(())
    })
    .await
}

pub async fn get_file_hashes(
    pool: &DbPool,
    project_id: i32,
) -> Result<HashMap<String, String>, AppError> {
    pool.with_conn(move |conn| {
        let mut stmt =
            conn.prepare("SELECT file_path, file_hash FROM file_hashes WHERE project_id = ?")?;
        let iter = stmt.query_map(params![project_id], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?;
        let mut hashes = HashMap::new();
        for r in iter {
            let (path, hash) = r?;
            hashes.insert(path, hash);
        }
        Ok(hashes)
    })
    .await
}

pub async fn remove_watched_project(pool: &DbPool, project_id: i32) -> Result<(), AppError> {
    pool.with_conn(move |conn| {
        // DuckDB does not support ON DELETE CASCADE; delete children explicitly.
        conn.execute(
            "DELETE FROM file_hashes WHERE project_id = ?",
            params![project_id],
        )?;
        conn.execute(
            "DELETE FROM watched_projects WHERE id = ?",
            params![project_id],
        )?;
        Ok(())
    })
    .await
}
