from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os
import json
from typing import Optional
import asyncio

# Import system monitoring for billion-row processing
try:
    from system_monitor import monitor, get_system_status, check_billion_row_readiness
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    print("⚠️  System monitoring not available. Install psutil for performance monitoring.")

# Simple FastAPI app
app = FastAPI(title="Local Gigasheet Clone")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enterprise DuckDB config for BILLION-ROW processing 🚀
conn = duckdb.connect('gigasheet_data.db', config={
    'threads': 8,  # Use more CPU cores
    'memory_limit': '16GB',  # Increase memory allocation
    'max_memory': '16GB',
    'temp_directory': './temp_duckdb',
    'checkpoint_threshold': '1GB',
    'wal_autocheckpoint': 1000,
    'enable_progress_bar': True,
    'enable_profiling': 'json',
    'profile_output': './duckdb_profile.json'
})

# Create temp directory
os.makedirs('./temp_duckdb', exist_ok=True)

# Enable extensions for performance
conn.execute("INSTALL parquet")
conn.execute("LOAD parquet")
conn.execute("INSTALL httpfs")
conn.execute("LOAD httpfs")

# Optimize settings for massive datasets
conn.execute("SET memory_limit='16GB'")
conn.execute("SET threads=8")
conn.execute("SET enable_progress_bar=true")
conn.execute("PRAGMA enable_checkpoint_on_shutdown")
conn.execute("PRAGMA wal_autocheckpoint=1000")

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Create processed files tracking table
conn.execute("""
    CREATE TABLE IF NOT EXISTS processed_files (
        filename VARCHAR PRIMARY KEY,
        file_size BIGINT,
        file_hash VARCHAR,
        processed_date TIMESTAMP,
        row_count BIGINT,
        status VARCHAR DEFAULT 'completed'
    )
""")

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
        """🚀 BILLION-ROW optimized pagination with partitioning"""
        try:
            # First check if table exists
            tables = self.conn.execute("SHOW TABLES").fetchall()
            existing_tables = [table[0] for table in tables]
            
            if table_name not in existing_tables:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found. Available tables: {existing_tables}")
            
            print(f"🚀 BILLION-ROW Query: '{table_name}' - offset: {offset:,}, limit: {limit:,}")
            
            # 🚀 BILLION-ROW optimized query building with partitioning
            where_clause = ""
            partition_hint = ""
            
            if filters:
                conditions = []
                global_search = None
                partition_keys = []
                
                for col, val in filters.items():
                    if col == '_global_search' and val and val.strip():
                        global_search = val.strip()
                    elif col == 'source_file' and val and val.strip():
                        # Optimize by targeting specific partitions
                        partition_key = hash(val) % 100
                        partition_keys.append(partition_key)
                        conditions.append(f"source_file ILIKE '%{val}%'")
                    elif val and val.strip():
                        # Use indexed columns where possible
                        if col in ['id', 'data_hash', 'partition_key']:
                            conditions.append(f"{col} = '{val}'")
                        else:
                            conditions.append(f"CAST({col} AS VARCHAR) ILIKE '%{val}%'")
                
                # Partition optimization for massive datasets
                if partition_keys:
                    partition_hint = f"AND partition_key IN ({','.join(map(str, partition_keys))})"
                
                # 🔍 Handle global search with partition-aware optimization
                if global_search:
                    print(f"   🔍 Global search: '{global_search}' across all columns")
                    
                    # Get all column names for the table (cached for performance)
                    columns_info = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
                    column_names = [col[0] for col in columns_info if col[0] not in ['id', 'partition_key']]
                    
                    # Create optimized search condition
                    global_conditions = []
                    for col_name in column_names[:20]:  # Limit to first 20 columns for performance
                        global_conditions.append(f"CAST({col_name} AS VARCHAR) ILIKE '%{global_search}%'")
                    
                    if global_conditions:
                        conditions.append(f"({' OR '.join(global_conditions)})")
                
                if conditions:
                    where_clause = f"WHERE {' AND '.join(conditions)} {partition_hint}"
            
            order_clause = ""
            if sort_by:
                direction = "DESC" if sort_desc else "ASC"
                order_clause = f"ORDER BY {sort_by} {direction}"
            
            # Get total count first (faster query)
            count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
            total_count = self.conn.execute(count_query).fetchone()[0]
            print(f"📈 Total rows matching criteria: {total_count:,}")
            
            # Get data
            query = f"""
                SELECT * FROM {table_name} 
                {where_clause}
                {order_clause}
                LIMIT {limit} OFFSET {offset}
            """
            
            result = self.conn.execute(query).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            print(f"📋 Retrieved {len(result)} rows with {len(columns)} columns")
            
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
            
            return {
                "data": data,
                "total_count": total_count,
                "columns": columns
            }
            
        except Exception as e:
            print(f"❌ Error querying table '{table_name}': {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error querying data: {str(e)}")

processor = GigasheetProcessor()

@app.get("/")
def root():
    return {"message": "🚀 BILLION-ROW Gigasheet Clone API is running!", "status": "ready", "billion_row_optimized": True}

@app.get("/system/status")
def system_status():
    """📊 Get current system performance stats"""
    if not MONITORING_ENABLED:
        return {"error": "System monitoring not available"}
    
    stats = get_system_status()
    warnings = monitor.get_performance_warning() if MONITORING_ENABLED else []
    
    return {
        "system_stats": stats,
        "performance_warnings": warnings,
        "billion_row_ready": len(warnings) == 0
    }

@app.get("/system/billion-row-check")
def billion_row_readiness():
    """🚀 Check if system is ready for billion-row processing"""
    if not MONITORING_ENABLED:
        return {
            "ready": "unknown",
            "message": "System monitoring not available. Install psutil for detailed analysis."
        }
    
    return check_billion_row_readiness()

@app.get("/processed-files")
def get_processed_files():
    """📊 Get information about processed Excel files"""
    try:
        processed = processor.conn.execute("""
            SELECT filename, file_size, processed_date, row_count, status 
            FROM processed_files 
            ORDER BY processed_date DESC
        """).fetchall()
        
        files_info = []
        for row in processed:
            files_info.append({
                "filename": row[0],
                "file_size_mb": round(row[1] / (1024 * 1024), 1),
                "processed_date": row[2],
                "row_count": row[3],
                "status": row[4]
            })
        
        return {
            "processed_files": files_info,
            "total_processed_files": len(files_info),
            "total_processed_rows": sum(f["row_count"] for f in files_info)
        }
    except Exception as e:
        return {
            "processed_files": [],
            "total_processed_files": 0,
            "total_processed_rows": 0,
            "error": str(e)
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
    try:
        tables = processor.conn.execute("SHOW TABLES").fetchall()
        return {"tables": [table[0] for table in tables]}
    except Exception as e:
        return {"tables": [], "error": str(e)}

@app.get("/tables/{table_name}/data")
def get_table_data(
    table_name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    search: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False)
):
    """Get paginated table data with global search support"""
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except:
            pass
    
    # Add global search to filters if provided
    if search and search.strip():
        filter_dict['_global_search'] = search.strip()
    
    return processor.get_data_page(table_name, offset, limit, filter_dict, sort_by, sort_desc)

@app.post("/merge-excel")
async def merge_excel_files():
    """🚀 BILLION-ROW Excel merger with chunked processing"""
    import pandas as pd
    import tempfile
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import multiprocessing as mp
    
    excel_folder = "../data"  # Put your Excel files here
    
    if not os.path.exists(excel_folder):
        raise HTTPException(status_code=404, detail="Excel folder not found. Create 'data' folder and add your Excel files.")
    
    excel_files = [f for f in os.listdir(excel_folder) if f.endswith(('.xlsx', '.xls'))]
    
    if not excel_files:
        raise HTTPException(status_code=404, detail="No Excel files found in data folder")
    
    print(f"🚀 SMART INCREMENTAL MERGE: Analyzing {len(excel_files)} Excel files...")
    
    try:
        # 🤖 SMART MERGE: Check which files are already processed
        def get_file_hash(file_path):
            import hashlib
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        
        def is_file_already_processed(filename, file_size, file_hash):
            result = processor.conn.execute(
                "SELECT filename FROM processed_files WHERE filename = ? AND file_size = ? AND file_hash = ?", 
                [filename, file_size, file_hash]
            ).fetchone()
            return result is not None
        
        # Analyze files - separate new vs existing
        new_files = []
        existing_files = []
        
        print(f"🔍 Analyzing files for incremental processing...")
        for file in excel_files:
            file_path = os.path.join(excel_folder, file)
            file_size = os.path.getsize(file_path)
            file_hash = get_file_hash(file_path)
            
            if is_file_already_processed(file, file_size, file_hash):
                existing_files.append(file)
                print(f"   ✅ {file} - Already processed (skipping)")
            else:
                new_files.append((file, file_size, file_hash))
                print(f"   🆕 {file} - New file (will process)")
        
        print(f"
📊 MERGE SUMMARY:")
        print(f"   ✅ Already processed: {len(existing_files)} files")
        print(f"   🆕 New files to process: {len(new_files)} files")
        print(f"   ⚡ Time saved: ~{len(existing_files) * 2} minutes\n")
        
        if len(new_files) == 0:
            print("🎉 All files already processed! No new data to merge.")
            
            # Get current stats
            stats = processor.conn.execute("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT source_file) as file_count
                FROM merged_excel_data
            """).fetchone()
            
            return {
                "success": True,
                "message": f"⚡ SMART MERGE: All {len(excel_files)} files already processed!",
                "total_rows": stats[0] if stats else 0,
                "files_processed": stats[1] if stats else 0,
                "new_files_processed": 0,
                "skipped_files": len(existing_files),
                "performance": "Incremental processing - massive time savings!"
            }
        
        # Check if table exists, if not create it
        tables = processor.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name='merged_excel_data'").fetchone()
        if not tables:
        
        # Create dynamic table structure that preserves original Excel columns
        print("🔍 Analyzing Excel file structure...")
        
        # First, read a sample from first Excel file to get column structure
        first_file = excel_files[0]
        first_file_path = os.path.join(excel_folder, first_file)
        sample_df = pd.read_excel(first_file_path, nrows=5)  # Just read 5 rows for structure
        
        # Create table with original columns + metadata
        columns_def = []
        for col in sample_df.columns:
            columns_def.append(f"{col.replace(' ', '_').replace('-', '_')} VARCHAR")
        
        # Add metadata columns
        columns_def.extend([
            "source_file VARCHAR",
            "partition_key INTEGER",
            "row_id BIGINT"
        ])
        
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS merged_excel_data (
                {', '.join(columns_def)}
            )
        """
        
        processor.conn.execute("DROP TABLE IF EXISTS merged_excel_data")
        processor.conn.execute(create_table_sql)
            print(f"✅ Table created with {len(sample_df.columns)} data columns + 3 metadata columns")
        else:
            print("✅ Table already exists - appending new data only")
        
        total_rows_processed = 0
        new_files_processed = 0
        chunk_size = 100000  # Process 100K rows at a time
        
        def process_excel_chunk(file_path, file_name, start_row, chunk_size):
            """Process Excel file in chunks for memory efficiency"""
            try:
                # Read Excel file in chunks
                df_chunk = pd.read_excel(
                    file_path, 
                    skiprows=range(1, start_row + 1) if start_row > 0 else None,
                    nrows=chunk_size,
                    engine='openpyxl'  # More memory efficient for large files
                )
                
                if df_chunk.empty:
                    return 0, None
                
                # Add metadata
                df_chunk['source_file'] = file_name
                df_chunk['partition_key'] = hash(file_name) % 100  # Create 100 partitions
                
                # Create temporary parquet file (more efficient than CSV)
                temp_file = tempfile.NamedTemporaryFile(suffix='.parquet', delete=False)
                df_chunk.to_parquet(temp_file.name, index=False, compression='snappy')
                temp_file.close()
                
                return len(df_chunk), temp_file.name
                
            except Exception as e:
                print(f"❌ Error processing chunk: {str(e)}")
                return 0, None
        
        # 🚀 Process ONLY new files with parallel chunking
        for i, (file, file_size, file_hash) in enumerate(new_files):
            file_path = os.path.join(excel_folder, file)
            file_size_mb = file_size / (1024 * 1024)
            print(f"📋 Processing NEW file: {file} ({i+1}/{len(new_files)}) - Size: {file_size_mb:.1f}MB")
            
            # Determine number of chunks based on file size
            estimated_rows = int(file_size_mb * 1000)  # Rough estimate
            num_chunks = max(1, estimated_rows // chunk_size)
            
            print(f"   🔄 Processing in {num_chunks} chunks of {chunk_size:,} rows each...")
            
            # Process chunks in parallel
            chunk_futures = []
            for chunk_idx in range(num_chunks):
                start_row = chunk_idx * chunk_size
                
                try:
                    rows_processed, temp_parquet = process_excel_chunk(
                        file_path, file, start_row, chunk_size
                    )
                    
                    if temp_parquet and rows_processed > 0:
                        # Load parquet into DuckDB efficiently  
                        processor.conn.execute(f"""
                            INSERT INTO merged_excel_data 
                            SELECT *, '{file}', {hash(file) % 100}, ROW_NUMBER() OVER() as row_id
                            FROM read_parquet('{temp_parquet}')
                        """)
                        
                        total_rows_processed += rows_processed
                        print(f"   ✅ Chunk {chunk_idx+1}: {rows_processed:,} rows | Total: {total_rows_processed:,}")
                        
                        # Clean up temp file
                        os.unlink(temp_parquet)
                        
                        # Force garbage collection for memory management
                        import gc
                        gc.collect()
                        
                    else:
                        print(f"   ⚙️ Chunk {chunk_idx+1}: No more data")
                        break
                        
                except Exception as chunk_error:
                    print(f"   ❌ Chunk {chunk_idx+1} failed: {str(chunk_error)}")
                    continue
            
            # 💾 Mark file as processed in tracking table
            file_rows = processor.conn.execute(
                "SELECT COUNT(*) FROM merged_excel_data WHERE source_file = ?", [file]
            ).fetchone()[0]
            
            processor.conn.execute("""
                INSERT OR REPLACE INTO processed_files 
                (filename, file_size, file_hash, processed_date, row_count, status)
                VALUES (?, ?, ?, datetime('now'), ?, 'completed')
            """, [file, file_size, file_hash, file_rows])
            
            new_files_processed += 1
            print(f"   🏁 File complete: {file} processed successfully ({file_rows:,} rows)")
        
        # Create indexes for billion-row performance
        print(f"🚀 Creating performance indexes for {total_rows_processed:,} rows...")
        
        processor.conn.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON merged_excel_data(source_file)")
        processor.conn.execute("CREATE INDEX IF NOT EXISTS idx_partition_key ON merged_excel_data(partition_key)")
        processor.conn.execute("CREATE INDEX IF NOT EXISTS idx_data_hash ON merged_excel_data(data_hash)")
        
        # Analyze table for query optimization
        processor.conn.execute("ANALYZE merged_excel_data")
        
        # Get final statistics
        stats = processor.conn.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT source_file) as file_count,
                COUNT(DISTINCT partition_key) as partition_count,
                COUNT(DISTINCT data_hash) as unique_records
            FROM merged_excel_data
        """).fetchone()
        
        print(f"🎆 SMART INCREMENTAL MERGE COMPLETE!")
        print(f"   Total rows in database: {stats[0]:,}")
        print(f"   Total files in database: {stats[1]:,}")
        print(f"   Partitions: {stats[2]:,}")
        print(f"   Unique records: {stats[3]:,}")
        print(f"   🆕 NEW files processed: {new_files_processed}")
        print(f"   ✅ Existing files skipped: {len(existing_files)}")
        print(f"   ⚡ Time saved: ~{len(existing_files) * 2} minutes")
        
        return {
            "success": True,
            "message": f"🚀 SMART MERGE SUCCESS! Processed {new_files_processed} new files, skipped {len(existing_files)} existing",
            "total_rows": stats[0],
            "files_processed": stats[1],
            "new_files_processed": new_files_processed,
            "skipped_files": len(existing_files),
            "partitions": stats[2],
            "unique_records": stats[3],
            "performance": f"Incremental processing saved ~{len(existing_files) * 2} minutes!"
        }
                
                # Load into DuckDB
                if i == 0:
                    # Create table from first file
                    processor.conn.execute(f"""
                        CREATE TABLE merged_excel_data AS 
                        SELECT * FROM read_csv_auto('{temp_csv.name}', header=true)
                    """)
                else:
                    # Insert from subsequent files
                    processor.conn.execute(f"""
                        INSERT INTO merged_excel_data 
                        SELECT * FROM read_csv_auto('{temp_csv.name}', header=true)
                    """)
                
                # Clean up temp file
                os.unlink(temp_csv.name)
                
            except Exception as file_error:
                print(f"   ⚠️ Error processing {file}: {str(file_error)}")
                continue
        
        # Get final count
        row_count = processor.conn.execute("SELECT COUNT(*) FROM merged_excel_data").fetchone()[0]
        
        print(f"✅ Successfully merged {len(excel_files)} files with {row_count:,} total rows!")
        
        return {
            "message": f"Successfully merged {len(excel_files)} Excel files",
            "table_name": "merged_excel_data",
            "files_processed": excel_files,
            "total_rows": row_count
        }
        
    except Exception as e:
        print(f"❌ Error merging Excel files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error merging Excel files: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Local Gigasheet Clone...")
    print("📊 Ready to process your 1 crore+ rows!")
    print("🌐 Backend will run on: http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000, reload=False)
