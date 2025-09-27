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

print(f"📊 Using persistent database: {DB_FILE}")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("uploads", exist_ok=True)
    print("🚀 Local Gigasheet Clone started!")
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
        "message": "🚀 Local Gigasheet Clone API",
        "version": "2.0",
        "features": {
            "persistent_storage": True,
            "32gb_ram_optimized": True,
            "export_formats": ["CSV", "Parquet", "Excel"],
            "backup_system": True
        },
        "endpoints": {
            "database_status": "/database/status",
            "system_status": "/system/status",
            "tables": "/tables",
            "documentation": "/docs"
        },
        "frontend": "http://localhost:3000"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process large CSV files"""
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files supported")
    
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process with DuckDB
    table_name = file.filename.replace('.csv', '').replace('-', '_').replace(' ', '_').lower()
    result = await processor.process_csv_file(file_path, table_name)
    
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
    
    print(f"🚀 Processing {len(excel_files)} Excel files...")
    
    # Drop existing table
    processor.conn.execute("DROP TABLE IF EXISTS merged_excel_data")
    
    all_dataframes = []
    total_rows_processed = 0
    
    for i, file in enumerate(excel_files):
        file_path = os.path.join(excel_folder, file)
        print(f"📊 Processing {file} ({i+1}/{len(excel_files)})...")
        
        try:
            # Read Excel file with pandas
            df = pd.read_excel(file_path)
            
            # Add source file column
            df['source_file'] = file
            
            # Add to list
            all_dataframes.append(df)
            total_rows_processed += len(df)
            
            print(f"✅ {file}: {len(df)} rows loaded")
            
        except Exception as e:
            print(f"❌ Error reading {file}: {str(e)}")
            continue
    
    if not all_dataframes:
        raise HTTPException(status_code=500, detail="No Excel files could be processed")
    
    # Combine all dataframes
    print("🔄 Combining all data...")
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
    
    print(f"✅ Successfully merged {len(excel_files)} files with {row_count} total rows")
    
    return {
        "message": f"Successfully merged {len(excel_files)} Excel files",
        "table_name": "merged_excel_data",
        "files_processed": excel_files,
        "total_rows": row_count
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
    print("🚀 Starting Local Gigasheet Backend...")
    print("📊 DuckDB initialized with enterprise config")
    print("🌐 Server will be available at: http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)
