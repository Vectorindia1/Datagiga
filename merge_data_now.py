#!/usr/bin/env python3
"""
Quick script to merge all data into one searchable table
Run this to create merged_all_data table for global search
"""
import pandas as pd
import duckdb
import os
import glob
from pathlib import Path

print("=" * 70)
print("🔗 MERGING ALL DATA INTO ONE TABLE")
print("=" * 70)

# Connect to the persistent database
DB_FILE = 'gigasheet_persistent.db'
conn = duckdb.connect(DB_FILE, config={
    'threads': 16,
    'memory_limit': '24GB',
    'max_memory': '28GB',
    'temp_directory': './temp_duckdb'
})

print(f"\n✅ Connected to database: {DB_FILE}")

all_dataframes = []
files_processed = []
errors = []

# Sources to scan
sources = [
    {"dir": "gigasheet-local/data", "patterns": ["*.xlsx", "*.xls", "*.csv", "*.txt"], "label": "data folder"},
    {"dir": "uploads", "patterns": ["*.xlsx", "*.xls", "*.csv", "*.txt"], "label": "uploads folder"}
]

print("\n📁 Scanning for data files...")

# Process files from directories
for source in sources:
    source_dir = source["dir"]
    if not os.path.exists(source_dir):
        print(f"⏭️  Skipping {source['label']} - not found")
        continue
    
    print(f"\n🔍 Scanning {source['label']}: {source_dir}")
    
    for pattern in source["patterns"]:
        files = glob.glob(os.path.join(source_dir, pattern))
        
        for file_path in files:
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Skip README files
            if 'README' in filename.upper():
                continue
            
            print(f"📄 Processing: {filename}...", end=" ")
            
            try:
                # Read file based on extension
                if file_ext in ['.xlsx', '.xls']:
                    print("(Excel)...", end=" ")
                    df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
                elif file_ext == '.csv':
                    print("(CSV)...", end=" ")
                    df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
                elif file_ext == '.txt':
                    print("(TXT)...", end=" ")
                    # Try tab-delimited first, then comma
                    try:
                        df = pd.read_csv(file_path, sep='\t', encoding='utf-8', on_bad_lines='skip')
                    except:
                        df = pd.read_csv(file_path, sep=',', encoding='utf-8', on_bad_lines='skip')
                else:
                    print("❌ Unsupported format")
                    continue
                
                # Add metadata columns
                df['_source_file'] = filename
                df['_source_folder'] = source['label']
                df['_file_type'] = file_ext
                
                all_dataframes.append(df)
                files_processed.append(filename)
                
                print(f"✅ {len(df):,} rows, {len(df.columns)} columns")
                
            except Exception as e:
                error_msg = f"{filename}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ Error: {str(e)}")

# Also include existing database tables
print("\n🗄️  Checking existing database tables...")
try:
    existing_tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    print(f"Found {len(existing_tables)} existing tables")
    
    excluded_tables = ['merged_all_data', 'merged_excel_data']
    for table_name in existing_tables:
        if table_name not in excluded_tables:
            try:
                print(f"📊 Including table: {table_name}...", end=" ")
                df = conn.execute(f"SELECT * FROM {table_name}").df()
                
                # Add metadata
                df['_source_file'] = f"table_{table_name}"
                df['_source_folder'] = "database"
                df['_file_type'] = ".table"
                
                all_dataframes.append(df)
                files_processed.append(f"table:{table_name}")
                
                print(f"✅ {len(df):,} rows")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
except Exception as e:
    print(f"⚠️  Could not check tables: {str(e)}")

# Check if we have data
if not all_dataframes:
    print("\n❌ ERROR: No data found to merge!")
    print("   Please:")
    print("   1. Upload files through the UI, OR")
    print("   2. Place files in gigasheet-local/data/ folder")
    exit(1)

print(f"\n🔄 Combining {len(all_dataframes)} data sources...")
print("   This may take a few minutes for large files...")

# Combine all dataframes
try:
    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    print(f"✅ Combined: {len(combined_df):,} total rows, {len(combined_df.columns)} columns")
except Exception as e:
    print(f"\n❌ ERROR combining data: {str(e)}")
    exit(1)

# Drop old table if exists
print("\n🗑️  Removing old merged_all_data table (if exists)...")
try:
    conn.execute("DROP TABLE IF EXISTS merged_all_data")
    print("✅ Old table removed")
except:
    pass

# Create new table
print("\n💾 Creating merged_all_data table in database...")
try:
    conn.register('temp_merged_all', combined_df)
    conn.execute("""
        CREATE TABLE merged_all_data AS 
        SELECT * FROM temp_merged_all
    """)
    conn.unregister('temp_merged_all')
    print("✅ Table created successfully!")
except Exception as e:
    print(f"❌ ERROR creating table: {str(e)}")
    exit(1)

# Get final statistics
row_count = conn.execute("SELECT COUNT(*) FROM merged_all_data").fetchone()[0]
column_count = len(conn.execute("DESCRIBE merged_all_data").fetchall())

print("\n" + "=" * 70)
print("🎉 MERGE COMPLETE!")
print("=" * 70)
print(f"\n📊 Statistics:")
print(f"   Sources merged:  {len(all_dataframes)}")
print(f"   Files processed: {len(files_processed)}")
print(f"   Total rows:      {row_count:,}")
print(f"   Total columns:   {column_count}")
print(f"\n📋 Table name: merged_all_data")

if errors:
    print(f"\n⚠️  Errors encountered: {len(errors)}")
    for err in errors[:5]:  # Show first 5 errors
        print(f"   • {err}")

print("\n✅ SUCCESS! You can now:")
print("   1. Go to Browse tab in the UI")
print("   2. Select 'merged_all_data' from dropdown")
print("   3. Use Global Search to search across ALL your data!")
print("\n" + "=" * 70)

conn.close()
