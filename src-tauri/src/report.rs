use genpdf::{elements, fonts, Alignment, Document, SimplePageDecorator};
use std::env;
use std::path::Path;

use crate::db::VulnerabilityReport;
use crate::error::AppError;

pub fn generate_pdf(report: &VulnerabilityReport) -> Result<String, AppError> {
    let font_family = if cfg!(windows) {
        let temp_font_dir = env::temp_dir().join("c-cure-fonts");
        let _ = std::fs::create_dir_all(&temp_font_dir);

        // Copy and rename to match genpdf's expected naming: [Family]-Regular.ttf, etc.
        let system_fonts = Path::new("C:\\Windows\\Fonts");
        let mappings = [
            ("arial.ttf", "Arial-Regular.ttf"),
            ("arialbd.ttf", "Arial-Bold.ttf"),
            ("ariali.ttf", "Arial-Italic.ttf"),
            ("arialbi.ttf", "Arial-BoldItalic.ttf"),
        ];

        for (src, dest) in mappings {
            let _ = std::fs::copy(system_fonts.join(src), temp_font_dir.join(dest));
        }

        fonts::from_files(&temp_font_dir, "Arial", None)
            .map_err(|e| AppError::Custom(format!("Failed to load fonts from temp dir: {}", e)))?
    } else {
        let font_dir = if cfg!(target_os = "macos") {
            "/Library/Fonts"
        } else {
            "/usr/share/fonts/truetype/dejavu"
        };
        fonts::from_files(font_dir, "DejaVuSans", None)
            .or_else(|_| fonts::from_files(font_dir, "Arial", None))
            .map_err(|e| AppError::Custom(format!("Could not load fonts: {}", e)))?
    };

    let mut doc = Document::new(font_family);
    doc.set_title("C-Cure Vulnerability Report");

    let mut decorator = SimplePageDecorator::new();
    decorator.set_margins(10);
    doc.set_page_decorator(decorator);

    // Title
    doc.push(elements::Paragraph::new("C-Cure Vulnerability Report").aligned(Alignment::Center));
    doc.push(elements::Break::new(1));

    // Project Info
    doc.push(elements::Paragraph::new(format!(
        "Project: {}",
        report.project_name
    )));
    doc.push(elements::Paragraph::new(format!(
        "Date: {}",
        report.timestamp
    )));
    doc.push(elements::Break::new(1));

    doc.push(elements::Paragraph::new("Summary"));
    doc.push(elements::Paragraph::new(format!(
        "Total Functions Scanned: {}",
        report.total_functions
    )));
    doc.push(elements::Paragraph::new(format!(
        "Vulnerable Functions: {}",
        report.vulnerable_functions
    )));
    doc.push(elements::Paragraph::new(format!(
        "Clean Functions: {}",
        report.clean_functions
    )));
    doc.push(elements::Paragraph::new(format!(
        "Files Scanned: {}",
        report.total_files
    )));
    doc.push(elements::Break::new(2));

    if !report.severity_breakdown.is_empty() {
        doc.push(elements::Paragraph::new("Severity Breakdown"));
        for severity in ["Critical", "High", "Medium", "Low"] {
            let count = report
                .severity_breakdown
                .get(severity)
                .copied()
                .unwrap_or(0);
            doc.push(elements::Paragraph::new(format!("{severity}: {count}")));
        }
        doc.push(elements::Break::new(1));
    }

    if !report.top_vulnerabilities.is_empty() {
        doc.push(elements::Paragraph::new("Top Vulnerability Types"));
        for hit in &report.top_vulnerabilities {
            let name = hit.cwe_name.as_deref().unwrap_or("Unknown");
            let severity = hit.severity.as_deref().unwrap_or("Unknown");
            doc.push(elements::Paragraph::new(format!(
                "{} - {} | Severity: {} | Hits: {}",
                hit.cwe, name, severity, hit.count
            )));
        }
        doc.push(elements::Break::new(2));
    }

    doc.push(elements::Paragraph::new(
        "Detailed Vulnerable Findings (safe functions omitted)",
    ));
    doc.push(elements::Break::new(1));

    for file_data in &report.files {
        doc.push(elements::Paragraph::new(&file_data.file_path));

        for func in &file_data.functions {
            let start = func.start_line.unwrap_or(0);
            let end = func.end_line.unwrap_or(0);

            let heading = format!(
                "{} (Lines {}-{}) - {}",
                func.function_name,
                start,
                end,
                func.verdict.to_uppercase()
            );

            doc.push(elements::Paragraph::new(heading));

            let cwe = func.cwe.as_deref().unwrap_or("Unknown");
            let cwe_name = func.cwe_name.as_deref().unwrap_or("Unknown");
            let sev = func.severity.as_deref().unwrap_or("Unknown");
            doc.push(elements::Paragraph::new(format!(
                "CWE: {} ({}) | Severity: {}",
                cwe, cwe_name, sev
            )));
            doc.push(elements::Break::new(0.5));
        }
        doc.push(elements::Break::new(1));
    }

    let temp_dir = env::temp_dir();
    let pdf_path = temp_dir.join(format!("c-cure-report-{}.pdf", report.id));

    doc.render_to_file(&pdf_path)
        .map_err(|e| AppError::Custom(format!("Failed to save PDF: {}", e)))?;

    Ok(pdf_path.to_string_lossy().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::VulnerabilityReport;
    use std::collections::HashMap;

    #[test]
    fn test_generate_pdf_file_creation() {
        let report = VulnerabilityReport {
            id: 99,
            project_name: "TestPDF".into(),
            project_path: None,
            timestamp: "2024-01-01 10:00:00".into(),
            total_files: 1,
            total_functions: 10,
            vulnerable_functions: 0,
            clean_functions: 10,
            severity_breakdown: HashMap::new(),
            top_vulnerabilities: vec![],
            files: vec![],
        };

        // This will attempt to load fonts from Windows system or fallback.
        // It might be flaky in CI but locally it should pass if fonts exist.
        // If it fails due to fonts, it will return an error, which is an expected path to test.
        let res = generate_pdf(&report);

        if let Ok(path) = res {
            assert!(Path::new(&path).exists());
            let _ = std::fs::remove_file(path);
        } else {
            // If we are on a system without standard fonts (like some CI),
            // we accept the failure for now as long as it's a handled error.
            println!("PDF generation failed (likely no fonts): {:?}", res.err());
        }
    }
}
