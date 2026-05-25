# C-Cure: LLM-Based C/C++ Vulnerability Scanner

[![Rust Backend](https://img.shields.io/badge/Backend-Rust-orange.svg)](https://www.rust-lang.org/)
[![Tauri Framework](https://img.shields.io/badge/Framework-Tauri_v2-blue.svg)](https://tauri.app/)
[![Svelte Frontend](https://img.shields.io/badge/Frontend-Svelte_5-ff3e00.svg)](https://svelte.dev/)
[![DuckDB Storage](https://img.shields.io/badge/Storage-DuckDB-fff000.svg)](https://duckdb.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**C-Cure** is a desktop application designed to streamline the identification of security vulnerabilities in C and C++ source code. By combining native AST parsing, asynchronous Rust orchestration, and external ML inference, C-Cure enables developers, security researchers, and students to detect critical flaws such as out-of-bounds access, integer overflow, double free, and null pointer dereference before they reach production.

Built on the **Tauri v2** framework with a high-performance **Rust backend**, C-Cure provides a lightweight, responsive, and cross-platform desktop experience with local analytical storage powered by **DuckDB**.

---

## Table of Contents

- [Key Features](#key-features)
- [Application Architecture](#application-architecture)
- [Project Structure](#project-structure)
- [Methodology & Workflow](#methodology--workflow)
- [Vulnerability Coverage](#vulnerability-coverage)
- [Prerequisites](#prerequisites)
- [Installation & Usage](#installation--usage)
- [Unit Testing](#unit-testing)
- [Contact](#contact)

---

## Key Features

### Smart Static Analysis
C-Cure uses specialized AST (Abstract Syntax Tree) parsing to break down C and C++ files into logical functions. This allows for granular security analysis of code blocks, improving accuracy and reducing noise compared to traditional line-by-line scanners.

### Optimized Report Navigation
Large analyses are stored in DuckDB and loaded through paginated report endpoints. The full report view fetches only the current slice of function rows, keeping navigation responsive even when a project contains a very large number of extracted functions.

### Interactive Security Dashboard
Monitor your project's security posture in real-time. The built-in dashboard provides visual metrics on total analyses, scanned files, vulnerable functions, severity distributions, CWE frequency, file-level safe/vulnerable ratios, and vulnerability trends over time.

### Continuous Folder Monitoring
Register your project directories to track changes automatically. C-Cure uses MD5 baseline hashing to detect added, modified, and deleted C/C++ files, allowing you to re-analyze only what has changed, saving time and resources.

### Professional PDF Reporting
Export detailed vulnerability assessment reports with a single click. Every report includes project metadata, summary metrics, severity breakdowns, top vulnerability types, CWE identifications, affected functions, and line ranges, formatted for professional distribution.

### Premium User Experience
Enjoy a modern, responsive interface built with Svelte 5 and Tailwind CSS. The app features optimized navigation, Chart.js visualizations, syntax-highlighted code views, searchable and filterable reports, and a unified dark-mode aesthetic for comfortable development.

---

## Application Architecture

| Layer | Component | Description |
|-------|-----------|-------------|
| **Frontend** | SvelteKit + Svelte 5 + Tailwind | A reactive desktop UI managing analysis setup, dashboards, monitoring, settings, history, and paginated report views. |
| **Shell** | Tauri v2 | Native application shell exposing secure IPC commands, file dialogs, path opening, and bundled desktop distribution. |
| **Logic Engine** | Rust + Tokio | Asynchronous backend handling orchestration, file system I/O, inference dispatch, report generation, and application state. |
| **Parser** | Tree-sitter C++ | Industrial-grade parser for C/C++ function extraction, including templates, source ranges, and code normalization. |
| **Inference Layer** | Reqwest + Kaggle/NGROK API | Configurable remote inference provider that classifies extracted snippets and maps model output to CWE metadata. |
| **Persistence** | DuckDB + async-duckdb | Local analytical database for analyses, files, functions, watched projects, file hashes, statistics, pagination, and reporting pipelines. |
| **Reporting** | genpdf | Native PDF generation for vulnerability-focused assessment reports. |

---

## Project Structure

```text
.
|-- src/                         # Frontend Application (SvelteKit)
|   |-- lib/                     # Shared stores, UI components, themes, CWE metadata, and utilities
|   `-- routes/                  # Application pages (Analyze, Statistics, Monitor, History, Reports, Settings)
|-- src-tauri/                   # Native Backend (Rust + Tauri)
|   |-- src/
|   |   |-- commands.rs          # Tauri IPC command surface
|   |   |-- parser.rs            # Tree-sitter function extraction and source normalization
|   |   |-- monitor.rs           # Hash-based project monitoring
|   |   |-- report.rs            # Native PDF generation
|   |   |-- db/                  # DuckDB schema, migration, repositories, pagination, and statistics
|   |   |-- inference/           # Kaggle provider, mock provider, settings, and async dispatcher
|   |   `-- services/            # Analysis orchestration services
|   |-- capabilities/            # Tauri permission capabilities
|   |-- icons/                   # Application icons
|   `-- Cargo.toml               # Backend dependency manifest
|-- static/                      # Static frontend assets
|-- test_project/                # Demo analysis target project
|-- package.json                 # Frontend dependency manifest and scripts
`-- README.md
```

---

## Methodology & Workflow

1.  **Scanning**: The user selects a single source file or a project folder for analysis.
2.  **Extraction**: The Rust backend uses `tree-sitter` to identify C/C++ function definitions, capture line ranges, and normalize function bodies before inference.
3.  **Inference**: Extracted function snippets are dispatched asynchronously to the configured Kaggle/NGROK inference API with bounded concurrency. The provider classifies each block as **Safe** or **Vulnerable** and returns confidence data.
4.  **Enrichment**: Vulnerable outputs are mapped to CWE names, default severities, CVSS-oriented frontend metadata, and remediation guidance.
5.  **Persistence**: Analysis metadata, scanned files, function results, watched projects, and file hashes are stored locally in DuckDB. Legacy SQLite data is migrated automatically when detected.
6.  **Reporting**: Summary screens load aggregate metrics, while detailed reports use optimized count and page endpoints. PDF export generates vulnerability-focused reports from the stored DuckDB results.

---

## Vulnerability Coverage

C-Cure maps code vulnerabilities to standard **Common Weakness Enumerations (CWE)**:

| ID | Description | Default Severity |
|----|-------------|------------------|
| **CWE-125** | Out-of-bounds Read | High |
| **CWE-787** | Out-of-bounds Write | Critical |
| **CWE-190** | Integer Overflow or Wraparound | High |
| **CWE-369** | Divide By Zero | Medium |
| **CWE-415** | Double Free | High |
| **CWE-476** | NULL Pointer Dereference | High |

---

## Prerequisites

- **Node.js**: Version 20+
- **Rust**: Stable toolchain (via `rustup`)
- **C++ Build Tools**: MSVC (Windows) or GCC/Clang (Linux/macOS) for native Rust dependencies.
- **Inference Endpoint**: A valid Kaggle/NGROK URL configured in the app's settings.

---

## Installation & Usage

1.  **Clone & Install**
    ```bash
    git clone https://github.com/LoayElHattab/C-Cure.git
    cd C-Cure
    npm install
    ```

2.  **Run Development Environment**
    ```bash
    npm run tauri dev
    ```

3.  **Run UI Only**
    ```bash
    npm run dev
    ```

4.  **Setup Inference**
    Open the application, go to **Settings**, and enter your remote Inference API URL.

5.  **Build Desktop Bundle**
    ```bash
    npm run tauri build
    ```

---

## Unit Testing

Run the frontend type and Svelte checks:

```bash
npm run check
```

Run the Rust unit tests:

```bash
cd src-tauri
cargo test
```

---

## Contact

For questions or collaboration inquiries, please open an issue in the project repository.
