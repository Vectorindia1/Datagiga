from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import duckdb
import os
import json
from typing import Optional
import asyncio
import pandas as pd


# Initialize PERSISTENT DuckDB - Optimized for 32GB RAM System! 🚀
DB_FILE = 'gigasheet_persistent.db'
conn = duckdb.connect(DB_FILE, config={
    'threads': 16,              # Use more threads for parallel processing
    'memory_limit': '24GB',     # Use 24GB of your 32GB RAM
    'max_memory': '28GB',       # Peak usage up to 28GB
    'temp_directory': './temp_duckdb'
})

# Install and load extensions
try:
    conn.execute("INSTALL spatial; LOAD spatial;")
except:
    pass  # Extension might already be installed

print(f"[DB] Using persistent database: {DB_FILE}")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("uploads", exist_ok=True)
    print("[STARTUP] Local Gigasheet Clone started!")
    yield
    # Shutdown
    pass

app = FastAPI(title="Local Gigasheet Clone", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GigasheetProcessor:
    def __init__(self):
        self.conn = conn
    
    async def process_csv_file(self, file_path: str, table_name: str):
        """Process CSV with DuckDB for maximum performance"""
        try:
            # DuckDB's read_csv_auto is extremely fast and robust
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{file_path}', 
                    header=true, 
                    ignore_errors=true,
                    max_line_size=1048576)
            """)
            
            # Get table info
            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            columns = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            
            return {
                "success": True,
                "table_name": table_name,
                "row_count": row_count,
                "columns": [{"name": col[0], "type": col[1]} for col in columns]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    async def process_file(self, file_path: str, table_name: str, file_extension: str):
        """Process different file formats (CSV, Excel, TXT)"""
        try:
            print(f"[PROCESSING] File: {file_path}, Type: {file_extension}")
            
            if file_extension in ['.csv', '.txt']:
                # Use DuckDB's fast CSV reader
                # For .txt files, we'll try to auto-detect delimiter
                self.conn.execute(f"""
                    CREATE OR REPLACE TABLE {table_name} AS 
                    SELECT * FROM read_csv_auto('{file_path}', 
                        header=true, 
                        ignore_errors=true,
                        max_line_size=1048576)
                """)
                
            elif file_extension in ['.xlsx', '.xls']:
                # Use pandas for Excel files with optimization
                import pandas as pd
                print(f"[EXCEL] Reading Excel file: {file_path}")
                
                # Get file size for progress indication
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"[EXCEL] File size: {file_size_mb:.2f} MB")
                
                # Read Excel file with engine selection
                if file_extension == '.xlsx':
                    df = pd.read_excel(file_path, engine='openpyxl')
                else:
                    df = pd.read_excel(file_path, engine='xlrd')
                    
                print(f"[EXCEL] Loaded {len(df):,} rows, {len(df.columns)} columns")
                
                # Register with DuckDB and create table
                print(f"[EXCEL] Creating table in DuckDB...")
                self.conn.register('temp_excel_data', df)
                self.conn.execute(f"""
                    CREATE OR REPLACE TABLE {table_name} AS 
                    SELECT * FROM temp_excel_data
                """)
                self.conn.unregister('temp_excel_data')
                print(f"[EXCEL] Table created successfully")
                
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")
            
            # Get table info
            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            columns = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            
            print(f"[SUCCESS] Table created: {table_name} ({row_count} rows, {len(columns)} columns)")
            
            return {
                "success": True,
                "table_name": table_name,
                "row_count": row_count,
                "columns": [{"name": col[0], "type": col[1]} for col in columns],
                "file_type": file_extension
            }
        except Exception as e:
            print(f"[ERROR] Failed to process file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    def get_data_page(self, table_name: str, offset: int = 0, limit: int = 1000,
                      filters: dict = None, sort_by: str = None, sort_desc: bool = False):
        """Get paginated data with server-side filtering"""
        try:
            # Build query
            where_clause = ""
            if filters:
                conditions = []
                for col, val in filters.items():
                    if val and val.strip():
                        # Use ILIKE for case-insensitive search
                        conditions.append(f"CAST({col} AS VARCHAR) ILIKE '%{val}%'")
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            order_clause = ""
            if sort_by:
                direction = "DESC" if sort_desc else "ASC"
                order_clause = f"ORDER BY {sort_by} {direction}"
            
            # Get data
            query = f"""
                SELECT * FROM {table_name} 
                {where_clause}
                {order_clause}
                LIMIT {limit} OFFSET {offset}
            """
            
            result = self.conn.execute(query).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            
            # Convert to JSON-serializable format
            data = []
            for row in result:
                row_dict = {}
                for i, val in enumerate(row):
                    # Handle different data types
                    if val is None:
                        row_dict[columns[i]] = None
                    elif isinstance(val, (int, float, str, bool)):
                        row_dict[columns[i]] = val
                    else:
                        row_dict[columns[i]] = str(val)
                data.append(row_dict)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
            total_count = self.conn.execute(count_query).fetchone()[0]
            
            return {
                "data": data,
                "total_count": total_count,
                "columns": columns
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error querying data: {str(e)}")

processor = GigasheetProcessor()

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Local Gigasheet Clone API",
        "version": "2.1",
        "features": {
            "persistent_storage": True,
            "32gb_ram_optimized": True,
            "supported_upload_formats": [".csv", ".xlsx", ".xls", ".txt"],
            "export_formats": ["CSV", "Parquet", "Excel"],
            "backup_system": True
        },
        "endpoints": {
            "upload": "/upload (POST - supports CSV, Excel, TXT)",
            "database_status": "/database/status",
            "system_status": "/system/status",
            "tables": "/tables",
            "documentation": "/docs"
        },
        "frontend": "http://localhost:3000"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process CSV, Excel (.xlsx, .xls), and TXT files"""
    
    # Get file extension
    filename_lower = file.filename.lower()
    file_extension = None
    
    # Supported formats
    supported_formats = ['.csv', '.xlsx', '.xls', '.txt']
    for ext in supported_formats:
        if filename_lower.endswith(ext):
            file_extension = ext
            break
    
    if not file_extension:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
        )
    
    print(f"[UPLOAD] Received file: {file.filename} (Type: {file_extension})")
    
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    print(f"[UPLOAD] File saved to: {file_path}")
    
    # Generate table name (remove extension and clean up)
    base_name = file.filename
    for ext in supported_formats:
        base_name = base_name.replace(ext, '').replace(ext.upper(), '')
    
    table_name = base_name.replace('-', '_').replace(' ', '_').replace('.', '_').lower()
    
    # Process file based on format
    result = await processor.process_file(file_path, table_name, file_extension)
    
    # Add info field to match frontend expectations
    result["info"] = {
        "row_count": result["row_count"],
        "columns": result["columns"]
    }
    
    return result

@app.get("/tables")
def list_tables():
    """List all available tables"""
    tables = processor.conn.execute("SHOW TABLES").fetchall()
    return {"tables": [table[0] for table in tables]}

@app.get("/tables/{table_name}/data")
def get_table_data(
    table_name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    filters: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False)
):
    """Get paginated table data"""
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except:
            pass
    
    return processor.get_data_page(table_name, offset, limit, filter_dict, sort_by, sort_desc)

@app.post("/merge-excel")
async def merge_excel_files():
    """Merge multiple Excel files using pandas (works without DuckDB Excel extension)"""
    import pandas as pd
    
    excel_folder = "../data"  # Put your Excel files here
    
    if not os.path.exists(excel_folder):
        raise HTTPException(status_code=404, detail="Excel folder not found. Create 'data' folder and add your Excel files.")
    
    excel_files = [f for f in os.listdir(excel_folder) if f.endswith(('.xlsx', '.xls'))]
    
    if not excel_files:
        raise HTTPException(status_code=404, detail="No Excel files found in data folder")
    
    print(f"[MERGE] Processing {len(excel_files)} Excel files...")
    
    # Drop existing table
    processor.conn.execute("DROP TABLE IF EXISTS merged_excel_data")
    
    all_dataframes = []
    total_rows_processed = 0
    
    for i, file in enumerate(excel_files):
        file_path = os.path.join(excel_folder, file)
        print(f"[EXCEL] Processing {file} ({i+1}/{len(excel_files)})...")
        
        try:
            # Read Excel file with pandas
            df = pd.read_excel(file_path)
            
            # Add source file column
            df['source_file'] = file
            
            # Add to list
            all_dataframes.append(df)
            total_rows_processed += len(df)
            
            print(f"[SUCCESS] {file}: {len(df)} rows loaded")
            
        except Exception as e:
            print(f"[ERROR] Error reading {file}: {str(e)}")
            continue
    
    if not all_dataframes:
        raise HTTPException(status_code=500, detail="No Excel files could be processed")
    
    # Combine all dataframes
    print("[MERGE] Combining all data...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Register the DataFrame with DuckDB
    processor.conn.register('merged_excel_data', combined_df)
    
    # Create persistent table
    processor.conn.execute("""
        CREATE TABLE merged_excel_data AS 
        SELECT * FROM merged_excel_data
    """)
    
    # Get final count
    row_count = processor.conn.execute("SELECT COUNT(*) FROM merged_excel_data").fetchone()[0]
    
    print(f"[SUCCESS] Successfully merged {len(excel_files)} files with {row_count} total rows")
    
    return {
        "message": f"Successfully merged {len(excel_files)} Excel files",
        "table_name": "merged_excel_data",
        "files_processed": excel_files,
        "total_rows": row_count
    }

@app.post("/merge-all-data")
async def merge_all_data():
    """Merge ALL data from all sources (Excel, CSV, TXT, uploaded files) into one master table"""
    import pandas as pd
    import glob
    
    print("[MERGE-ALL] Starting comprehensive data merge...")
    
    all_dataframes = []
    files_processed = []
    errors = []
    
    # Define source directories and file patterns
    sources = [
        {"dir": "../data", "patterns": ["*.xlsx", "*.xls", "*.csv", "*.txt"], "label": "data folder"},
        {"dir": "uploads", "patterns": ["*.xlsx", "*.xls", "*.csv", "*.txt"], "label": "uploads folder"}
    ]
    
    # Also merge existing tables from database
    try:
        existing_tables = [t[0] for t in processor.conn.execute("SHOW TABLES").fetchall()]
        print(f"[MERGE-ALL] Found {len(existing_tables)} existing tables in database")
    except:
        existing_tables = []
    
    # Process files from directories
    for source in sources:
        source_dir = source["dir"]
        if not os.path.exists(source_dir):
            print(f"[MERGE-ALL] Skipping {source['label']} - directory not found")
            continue
        
        print(f"[MERGE-ALL] Scanning {source['label']}: {source_dir}")
        
        for pattern in source["patterns"]:
            files = glob.glob(os.path.join(source_dir, pattern))
            
            for file_path in files:
                filename = os.path.basename(file_path)
                file_ext = os.path.splitext(filename)[1].lower()
                
                print(f"[MERGE-ALL] Processing: {filename}")
                
                try:
                    # Read file based on extension
                    if file_ext in ['.xlsx', '.xls']:
                        df = pd.read_excel(file_path)
                    elif file_ext == '.csv':
                        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
                    elif file_ext == '.txt':
                        # Try to read as CSV with different delimiters
                        try:
                            df = pd.read_csv(file_path, sep='\t', encoding='utf-8', on_bad_lines='skip')
                        except:
                            df = pd.read_csv(file_path, sep=',', encoding='utf-8', on_bad_lines='skip')
                    else:
                        continue
                    
                    # Add metadata columns
                    df['_source_file'] = filename
                    df['_source_folder'] = source['label']
                    df['_file_type'] = file_ext
                    
                    all_dataframes.append(df)
                    files_processed.append(filename)
                    
                    print(f"[SUCCESS] {filename}: {len(df)} rows, {len(df.columns)} columns")
                    
                except Exception as e:
                    error_msg = f"{filename}: {str(e)}"
                    errors.append(error_msg)
                    print(f"[ERROR] {error_msg}")
                    continue
    
    # Also include data from existing database tables (excluding the merge tables)
    excluded_tables = ['merged_all_data', 'merged_excel_data']
    for table_name in existing_tables:
        if table_name not in excluded_tables:
            try:
                print(f"[MERGE-ALL] Including existing table: {table_name}")
                df = processor.conn.execute(f"SELECT * FROM {table_name}").df()
                
                # Add metadata
                df['_source_file'] = f"table_{table_name}"
                df['_source_folder'] = "database"
                df['_file_type'] = ".table"
                
                all_dataframes.append(df)
                files_processed.append(f"table:{table_name}")
                
                print(f"[SUCCESS] Table {table_name}: {len(df)} rows")
            except Exception as e:
                error_msg = f"table:{table_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")
    
    # Check if we have any data to merge
    if not all_dataframes:
        raise HTTPException(
            status_code=404, 
            detail="No data found to merge. Please upload files or add them to the data folder."
        )
    
    print(f"[MERGE-ALL] Combining {len(all_dataframes)} data sources...")
    
    # Combine all dataframes with column alignment
    # Use outer join to include all columns from all sources
    try:
        combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
        print(f"[MERGE-ALL] Combined dataframe: {len(combined_df)} rows, {len(combined_df.columns)} columns")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error combining data: {str(e)}")
    
    # Drop the old merged_all_data table if it exists
    try:
        processor.conn.execute("DROP TABLE IF EXISTS merged_all_data")
    except:
        pass
    
    # Register and create persistent table
    try:
        processor.conn.register('temp_merged_all', combined_df)
        processor.conn.execute("""
            CREATE TABLE merged_all_data AS 
            SELECT * FROM temp_merged_all
        """)
        processor.conn.unregister('temp_merged_all')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating merged table: {str(e)}")
    
    # Get final statistics
    row_count = processor.conn.execute("SELECT COUNT(*) FROM merged_all_data").fetchone()[0]
    column_count = len(processor.conn.execute("DESCRIBE merged_all_data").fetchall())
    
    print(f"[SUCCESS] Merged all data: {row_count} rows, {column_count} columns")
    print(f"[MERGE-ALL] Files processed: {len(files_processed)}")
    if errors:
        print(f"[MERGE-ALL] Errors encountered: {len(errors)}")
    
    return {
        "message": f"Successfully merged all data from {len(files_processed)} sources",
        "table_name": "merged_all_data",
        "files_processed": files_processed,
        "total_rows": row_count,
        "total_columns": column_count,
        "sources_merged": len(all_dataframes),
        "errors": errors if errors else None,
        "note": "All your data is now in 'merged_all_data' table - search across everything!"
    }

# 💾 DATA PERSISTENCE & TRANSFER ENDPOINTS

@app.get("/database/status")
def get_database_status():
    """Get database file information and statistics"""
    try:
        # Get database file size
        db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
        
        # Get all tables with row counts
        tables = processor.conn.execute("SHOW TABLES").fetchall()
        table_info = []
        
        for table in tables:
            table_name = table[0]
            row_count = processor.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            table_info.append({
                "name": table_name,
                "row_count": row_count
            })
        
        return {
            "database_file": DB_FILE,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "tables": table_info,
            "total_tables": len(table_info),
            "total_rows": sum(t["row_count"] for t in table_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database status error: {str(e)}")

@app.post("/export/{table_name}")
def export_table(table_name: str, format: str = Query("csv", pattern="^(csv|parquet|excel)$")):
    """Export table to various formats for transfer to other devices"""
    try:
        # Verify table exists
        tables = [t[0] for t in processor.conn.execute("SHOW TABLES").fetchall()]
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Create exports directory
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            filename = f"{table_name}_{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            
            # Export to CSV using DuckDB's high-performance export
            processor.conn.execute(f"""
                COPY {table_name} TO '{filepath}' 
                (FORMAT CSV, HEADER TRUE, DELIMITER ',')
            """)
            
        elif format == "parquet":
            filename = f"{table_name}_{timestamp}.parquet"
            filepath = os.path.join(export_dir, filename)
            
            # Export to Parquet (most efficient format)
            processor.conn.execute(f"""
                COPY {table_name} TO '{filepath}' 
                (FORMAT PARQUET, COMPRESSION snappy)
            """)
            
        elif format == "excel":
            filename = f"{table_name}_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            # Export to Excel (slower but widely compatible)
            import pandas as pd
            df = processor.conn.execute(f"SELECT * FROM {table_name}").df()
            df.to_excel(filepath, index=False, engine='openpyxl')
        
        # Get file size
        file_size = os.path.getsize(filepath)
        row_count = processor.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        return {
            "message": f"Successfully exported {table_name} to {format.upper()}",
            "filename": filename,
            "filepath": filepath,
            "format": format,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "row_count": row_count,
            "export_time": timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/backup/create")
def create_full_backup():
    """Create a complete backup of the entire database for transfer"""
    try:
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"gigasheet_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create a backup by copying the database file
        import shutil
        shutil.copy2(DB_FILE, backup_path)
        
        # Get backup info
        backup_size = os.path.getsize(backup_path)
        tables = processor.conn.execute("SHOW TABLES").fetchall()
        
        return {
            "message": "Full database backup created successfully!",
            "backup_filename": backup_filename,
            "backup_path": backup_path,
            "backup_size_mb": round(backup_size / (1024 * 1024), 2),
            "tables_included": [t[0] for t in tables],
            "timestamp": timestamp,
            "instructions": {
                "transfer": f"Copy {backup_path} to another device",
                "restore": "Use /backup/restore endpoint with the backup file"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup error: {str(e)}")

@app.post("/backup/restore")
async def restore_from_backup(file: UploadFile = File(...)):
    """Restore database from backup file"""
    try:
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Only .db files are supported for restore")
        
        # Save uploaded backup file
        temp_backup_path = f"temp_restore_{file.filename}"
        with open(temp_backup_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Close current connection
        processor.conn.close()
        
        # Replace current database with backup
        import shutil
        shutil.copy2(temp_backup_path, DB_FILE)
        
        # Reconnect with new database
        global conn
        conn = duckdb.connect(DB_FILE, config={
            'threads': 16,
            'memory_limit': '24GB',
            'max_memory': '28GB',
            'temp_directory': './temp_duckdb'
        })
        processor.conn = conn
        
        # Clean up temp file
        os.remove(temp_backup_path)
        
        # Get restored database info
        tables = processor.conn.execute("SHOW TABLES").fetchall()
        total_rows = 0
        for table in tables:
            total_rows += processor.conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        
        return {
            "message": "Database restored successfully from backup!",
            "restored_from": file.filename,
            "tables_restored": [t[0] for t in tables],
            "total_rows": total_rows,
            "note": "All your previous data has been restored and will persist across restarts"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore error: {str(e)}")

# 🔍 GLOBAL SEARCH ENDPOINT

@app.get("/tables/{table_name}/search")
def global_search(
    table_name: str,
    query: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Search across all columns in a table for matching records"""
    try:
        # Verify table exists
        tables = [t[0] for t in processor.conn.execute("SHOW TABLES").fetchall()]
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get all columns from the table
        columns_result = processor.conn.execute(f"DESCRIBE {table_name}").fetchall()
        columns = [col[0] for col in columns_result]
        
        print(f"[SEARCH] Searching table '{table_name}' for: '{query}'")
        print(f"[SEARCH] Columns to search: {columns}")
        
        # Build search conditions for all columns
        # Use CAST to VARCHAR and ILIKE for case-insensitive search
        search_conditions = []
        for col in columns:
            # Escape single quotes in query for SQL safety
            safe_query = query.replace("'", "''")
            search_conditions.append(f"CAST({col} AS VARCHAR) ILIKE '%{safe_query}%'")
        
        # Combine all conditions with OR
        where_clause = " OR ".join(search_conditions)
        
        # Build the full query
        search_query = f"""
            SELECT * FROM {table_name}
            WHERE {where_clause}
            LIMIT {limit} OFFSET {offset}
        """
        
        # Execute search
        result = processor.conn.execute(search_query).fetchall()
        
        # Convert to JSON-serializable format
        data = []
        for row in result:
            row_dict = {}
            for i, val in enumerate(row):
                # Handle different data types
                if val is None:
                    row_dict[columns[i]] = None
                elif isinstance(val, (int, float, str, bool)):
                    row_dict[columns[i]] = val
                else:
                    row_dict[columns[i]] = str(val)
            data.append(row_dict)
        
        # Get total count of matching records
        count_query = f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {where_clause}
        """
        total_matches = processor.conn.execute(count_query).fetchone()[0]
        
        print(f"[SEARCH] Found {total_matches} matches, returning {len(data)} results")
        
        return {
            "query": query,
            "table_name": table_name,
            "data": data,
            "columns": columns,
            "total_matches": total_matches,
            "returned_count": len(data),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        print(f"[SEARCH ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/exports/list")
def list_exports():
    """List all available export files"""
    try:
        export_dir = "exports"
        if not os.path.exists(export_dir):
            return {"exports": [], "message": "No exports found"}
        
        exports = []
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                exports.append({
                    "filename": filename,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "created": os.path.getctime(filepath)
                })
        
        return {
            "exports": sorted(exports, key=lambda x: x["created"], reverse=True),
            "total_exports": len(exports)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List exports error: {str(e)}")

# 🚀 SYSTEM MONITORING ENDPOINTS

@app.get("/system/status")
def get_system_status():
    """Get system resource status for monitoring"""
    try:
        import psutil
        
        # Get system stats
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "status": "running",
            "system_stats": {
                "memory": {
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": psutil.cpu_count()
                }
            },
            "database": {
                "type": "DuckDB",
                "persistent": True,
                "ram_optimized": "32GB System - 24GB Allocated"
            }
        }
    except ImportError:
        return {
            "status": "running",
            "message": "psutil not available, basic status only",
            "database": {
                "type": "DuckDB", 
                "persistent": True,
                "ram_optimized": "32GB System - 24GB Allocated"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status error: {str(e)}")

@app.get("/system/billion-row-check")
def check_billion_row_readiness():
    """Check if system is ready for billion-row processing"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        # Check readiness criteria
        memory_ok = memory.available > 16 * (1024**3)  # 16GB available
        cpu_ok = cpu_count >= 8  # 8+ cores
        
        ready = memory_ok and cpu_ok
        
        return {
            "ready_for_billion_rows": ready,
            "checks": {
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "cpu_cores": cpu_count,
                "memory_check": memory_ok,
                "cpu_check": cpu_ok
            },
            "optimization_status": "32GB RAM System - Billion Row Ready!" if ready else "System may need optimization",
            "recommendations": [
                "Memory: 24GB allocated for processing",
                "Threads: 16 parallel processing enabled", 
                "Storage: Persistent DuckDB with SSD recommended"
            ]
        }
    except ImportError:
        # Fallback when psutil not available
        return {
            "ready_for_billion_rows": True,
            "message": "Assuming billion-row ready (psutil not available)",
            "optimization_status": "32GB RAM System - Optimized Configuration",
            "recommendations": [
                "DuckDB configured for 24GB RAM usage",
                "16-thread parallel processing enabled",
                "Persistent storage active"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Readiness check error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("[BACKEND] Starting Local Gigasheet Backend...")
    print("[DUCKDB] Initialized with enterprise config")
    print("[SERVER] Available at: http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)
