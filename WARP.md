# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- This repo contains a Python FastAPI backend that uses DuckDB for high-performance analytics on large CSV/Excel datasets. Code is under gigasheet-local/backend. A frontend is referenced in README.md but is not present in the repository.
- There are multiple backend entrypoints with slightly different capabilities and configurations:
  - backend/main.py: persistent DuckDB DB, export and backup endpoints, system status.
  - backend/working_main.py: smart incremental Excel merge with processed_files tracking.
  - backend/simple_main.py: similar to working_main with additional performance knobs and monitoring hooks.

Commands
- Environment setup (Windows PowerShell)
  ```powershell path=null start=null
  # From repo root
  py -3 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r gigasheet-local\backend\requirements.txt
  ```

- Run backend (choose one entrypoint)
  ```powershell path=null start=null
  # Default persistent backend (features: upload CSV, merge Excel, export, backup)
  python gigasheet-local\backend\main.py

  # Smart incremental merge backend (focus on Excel merging performance)
  python gigasheet-local\backend\working_main.py

  # Alternative backend with additional tuning/monitoring paths
  python gigasheet-local\backend\simple_main.py
  ```

- Quick health check (after server starts on http://localhost:8000)
  ```powershell path=null start=null
  Invoke-RestMethod http://localhost:8000/ | ConvertTo-Json -Depth 5
  ```

- Upload a CSV (multipart form field name: file)
  ```powershell path=null start=null
  $csv = Get-Item .\big.csv  # replace with your CSV path
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/upload -Form @{ file = $csv } | ConvertTo-Json -Depth 5
  ```

- List tables and page through data
  ```powershell path=null start=null
  # List tables
  Invoke-RestMethod http://localhost:8000/tables | ConvertTo-Json -Depth 5

  # Get first 1000 rows from a table (replace my_table)
  Invoke-RestMethod "http://localhost:8000/tables/my_table/data?limit=1000&offset=0" | ConvertTo-Json -Depth 5

  # Apply server-side filters (filters is JSON-encoded)
  $filters = @{ col1 = "abc"; col2 = "123" } | ConvertTo-Json -Compress
  $url = "http://localhost:8000/tables/my_table/data?limit=1000&offset=0&filters=$([uri]::EscapeDataString($filters))"
  Invoke-RestMethod $url | ConvertTo-Json -Depth 5
  ```

- Merge Excel files from gigasheet-local/data
  ```powershell path=null start=null
  # Ensure your .xlsx/.xls files are under gigasheet-local\data

  # main.py entrypoint
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/merge-excel | ConvertTo-Json -Depth 5

  # working_main.py entrypoint (smart incremental)
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/smart-merge-excel | ConvertTo-Json -Depth 5

  # working_main.py also supports a force rebuild that re-derives columns
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/force-rebuild-merge | ConvertTo-Json -Depth 5
  ```

- Export data and create/restore backups (main.py only)
  ```powershell path=null start=null
  # Export a table to CSV/Parquet/Excel (replace my_table)
  Invoke-RestMethod -Method Post -Uri "http://localhost:8000/export/my_table?format=parquet" | ConvertTo-Json -Depth 5

  # List exported files (written under gigasheet-local\backend\exports)
  Invoke-RestMethod http://localhost:8000/exports/list | ConvertTo-Json -Depth 5

  # Create a full DB backup (written under gigasheet-local\backend\backups)
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/backup/create | ConvertTo-Json -Depth 5

  # Restore from a .db backup file
  $db = Get-Item .\gigasheet-local\backend\backups\gigasheet_backup_YYYYmmdd_HHMMSS.db
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/backup/restore -Form @{ file = $db } | ConvertTo-Json -Depth 5
  ```

- Reset processed_files tracking (for reprocessing in working_main/simple_main flows)
  ```powershell path=null start=null
  python gigasheet-local\backend\reset_tracking.py
  ```

Notes about tests and linting
- No test suite or linter configuration is present in the repository. If/when pytest, flake8, ruff, or black are added, update this file with the exact commands and any project-specific options.

High-level architecture and structure
- FastAPI application
  - CORS is open to all origins.
  - The app runs at http://localhost:8000 and exposes endpoints for uploading CSVs, listing tables, paginated reads with filtering/sorting, Excel merging, and (in main.py) export and backup.

- DuckDB persistence and configuration
  - main.py uses a persistent database file gigasheet_persistent.db, with configuration tuned for a 32GB RAM system (threads=16, memory_limit ~24GB, max_memory ~28GB, temp directory ./temp_duckdb). It attempts to install/load the spatial extension.
  - working_main.py and simple_main.py use gigasheet_data.db with different memory/thread settings (e.g., threads=8, memory_limit=16GB). Both create ./temp_duckdb and an uploads directory.

- Data ingestion and query path
  - POST /upload accepts a CSV (multipart form field name file), saves under backend/uploads, and creates/overwrites a DuckDB table named from the CSV filename using read_csv_auto.
  - GET /tables enumerates DuckDB tables; GET /tables/{table}/data provides server-side pagination and filtering (filters is a JSON object, values matched with ILIKE against string casts). Sorting is optional via sort_by and sort_desc.

- Excel merge flows
  - main.py: POST /merge-excel reads all .xlsx/.xls from gigasheet-local/data using pandas, adds source_file, registers the combined DataFrame with DuckDB, and materializes it as merged_excel_data. Intended for full rebuilds.
  - working_main.py: Adds a processed_files table (filename, size, hash, processed_date, row_count, status) to enable incremental processing:
    - POST /smart-merge-excel processes only new files (based on size+hash), aligns columns, and appends to merged_excel_data. POST /force-rebuild-merge rebuilds the table by scanning columns across files first to lock a consistent schema.
  - simple_main.py: Similar intent to working_main with more performance-oriented settings and monitoring hooks; includes chunked/partition-aware comments and additional toggles.

- Monitoring and readiness
  - backend/system_monitor.py (psutil-based) provides system stats, warnings, and “billion-row readiness” checks. main.py/simple_main.py expose /system/status and /system/billion-row-check endpoints with varying fidelity depending on psutil availability.

- Persistence model and file layout
  - Database files (gigasheet_persistent.db or gigasheet_data.db) are created alongside backend code. Temporary files are written under backend/temp_duckdb. Exports are written to backend/exports, and backups to backend/backups (main.py).
  - The Excel merge expects input spreadsheets in gigasheet-local/data. The CSV upload flow writes to backend/uploads/ and creates a DuckDB table from that path.

Important notes from README.md
- README describes a React + AG Grid frontend (frontend folder) and Windows startup scripts (start.bat, start.ps1). These are not present in the repository. If you add the frontend, follow the README’s guidance (npm install, npm start on port 3000) and update this WARP.md with actual commands and paths.
- API endpoints in README (upload, tables, tables/{table}/data, merge-excel) match the backend implementations in this repo; additional endpoints exist in main.py for export and backup, and in working_main.py for smart/force merge.

CI, rules, and other tooling
- No CLAUDE, Cursor, or Copilot rules were found in the repo.
- No CI config files were found.

How to extend this file
- If you add tests, linters, formatters, or a frontend, update the Commands section with exact invocation patterns and relevant configs.
