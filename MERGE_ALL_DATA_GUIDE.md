# 🔗 Merge All Data Feature - Complete Guide

## Overview

The **Merge All Data** feature is the ultimate data consolidation tool! It combines **EVERYTHING** - all your uploaded files, data folder files, and existing database tables - into a single, searchable master table called `merged_all_data`.

---

## 🎯 What Gets Merged?

### Sources Included:

1. **📁 Data Folder** (`gigasheet-local/data/`)
   - Excel files (.xlsx, .xls)
   - CSV files (.csv)
   - Text files (.txt)

2. **📤 Uploads Folder** (`uploads/`)
   - All uploaded CSV files
   - All uploaded Excel files
   - All uploaded TXT files

3. **🗄️ Existing Database Tables**
   - Any tables you've already created
   - Previously uploaded data
   - All individual table data

### Result:

✅ **One Master Table**: `merged_all_data`  
✅ **All Your Data**: In one place  
✅ **Searchable**: Use Global Search to find anything  
✅ **Persistent**: Saved in database permanently  

---

## 🚀 How to Use

### Step-by-Step Process:

#### 1. Prepare Your Data

**Option A: Add files to data folder**
```
Place files in: D:\projects\GigaSheet\gigasheet-local\data\
- sales_2023.xlsx
- sales_2024.xlsx
- customers.csv
- inventory.txt
```

**Option B: Upload files via UI**
- Go to Upload tab
- Upload your CSV, Excel, or TXT files
- Files are stored in uploads folder

**Option C: Use existing tables**
- Already uploaded data? Perfect!
- Already merged Excel files? Great!
- All existing tables will be included

#### 2. Merge Everything

1. **Go to Upload Tab**
2. **Scroll to "Merge ALL Data" section** (highlighted card)
3. **Click "Merge All Data" button**
4. **Wait for processing** (may take minutes for large datasets)

#### 3. View Results

After merge completes:
- ✅ Success message shows sources merged
- 📊 Total rows and columns displayed
- 🔍 Table name: `merged_all_data`
- 🎉 Popup confirmation with details

#### 4. Search Your Data

1. **Go to Browse tab**
2. **Select "merged_all_data" from dropdown**
3. **Use Global Search to find anything!**
4. **Search across ALL your data at once!**

---

## ✨ Key Features

### 1. **Comprehensive Merging**
- Merges ALL file types (CSV, Excel, TXT)
- Includes uploaded AND data folder files
- Incorporates existing database tables
- One-click operation

### 2. **Smart Column Handling**
- Different files can have different columns
- Missing columns filled with NULL
- All columns preserved
- Column alignment handled automatically

### 3. **Metadata Tracking**
- **`_source_file`**: Original filename
- **`_source_folder`**: data folder, uploads folder, or database
- **`_file_type`**: .xlsx, .csv, .txt, or .table

### 4. **Error Handling**
- Continues if some files fail
- Reports errors after completion
- Shows which files succeeded
- Detailed error messages

### 5. **Performance Optimized**
- Processes files in batches
- Uses pandas for file reading
- DuckDB for fast storage
- Progress tracking in console

---

## 📊 Use Cases

### Use Case 1: Consolidate Multiple Years

**Scenario:** You have sales data from different years

```
Files:
- sales_2021.xlsx (10,000 rows)
- sales_2022.xlsx (15,000 rows)
- sales_2023.xlsx (20,000 rows)
- sales_2024.csv (25,000 rows)

Result:
- merged_all_data table with 70,000 rows
- Search "2023" to find all 2023 data
- Search "ProductX" across all years
```

### Use Case 2: Combine Different Datasets

**Scenario:** Customer data, orders, and inventory

```
Files:
- customers.csv (5,000 rows)
- orders.xlsx (50,000 rows)
- inventory.txt (10,000 rows)

Result:
- All data in one table
- Search by customer name, order ID, or product
- Cross-reference across datasets
```

### Use Case 3: Merge Uploaded and Folder Files

**Scenario:** Some files uploaded via UI, others in data folder

```
Uploaded:
- report_q1.csv
- report_q2.csv

Data Folder:
- report_q3.xlsx
- report_q4.xlsx

Result:
- All quarterly reports in one table
- Search any metric across all quarters
```

### Use Case 4: Include Existing Tables

**Scenario:** You've already processed some data

```
Existing Tables:
- customers_imported
- sales_2023
- inventory_current

New Files:
- sales_2024.xlsx
- new_customers.csv

Result:
- Everything merged together
- Historical + current data combined
```

---

## 🎨 UI Features

### Merge All Data Card

**Visual Elements:**
- 🔗 Header: "Merge ALL Data"
- Blue highlight border (stands out)
- Clear description
- Large action button
- Status display area
- Pro tip guidance

**Status Updates:**
- ⏳ Processing indicator during merge
- ✅ Success message with statistics
- ⚠️ Warning if some files failed
- ❌ Error messages if merge fails

**Post-Merge Display:**
```
✅ Successfully merged 8 data sources!
Total rows: 125,450
Total columns: 34
Table name: merged_all_data
```

---

## 🔧 Technical Details

### Backend Endpoint

```
POST /merge-all-data
```

**No parameters required** - automatically scans all sources

**Response:**
```json
{
  "message": "Successfully merged all data from 8 sources",
  "table_name": "merged_all_data",
  "files_processed": [
    "sales_2023.xlsx",
    "customers.csv",
    "inventory.txt",
    "table:orders"
  ],
  "total_rows": 125450,
  "total_columns": 34,
  "sources_merged": 8,
  "errors": null,
  "note": "All your data is now in 'merged_all_data' table - search across everything!"
}
```

### Processing Logic

1. **Scan Directories**
   - Check `gigasheet-local/data/`
   - Check `uploads/`
   - List existing database tables

2. **Read Files**
   - Excel: `pd.read_excel()`
   - CSV: `pd.read_csv()`
   - TXT: Auto-detect delimiter

3. **Add Metadata**
   - Source file name
   - Source folder/database
   - File type

4. **Combine Data**
   - Use pandas concat
   - Outer join (includes all columns)
   - Ignore index (create new)

5. **Create Table**
   - Register with DuckDB
   - Create persistent table
   - Get final statistics

### Column Alignment

**Example:**

File 1 has: Name, Age, City  
File 2 has: Name, Age, Country  
File 3 has: Name, Email

**Result table has:**
```
Name | Age | City | Country | Email | _source_file | _source_folder | _file_type
-----|-----|------|---------|-------|--------------|----------------|------------
John | 25  | NYC  | NULL    | NULL  | file1.csv    | uploads        | .csv
Jane | 30  | NULL | USA     | NULL  | file2.xlsx   | data folder    | .xlsx
Bob  | NULL| NULL | NULL    | bob@  | file3.txt    | uploads        | .txt
```

---

## 💡 Best Practices

### Before Merging

1. **Check File Formats**
   - Ensure files are .csv, .xlsx, .xls, or .txt
   - Clean data if possible
   - Remove unnecessary files

2. **Organize Files**
   - Put related files in data folder
   - Name files descriptively
   - Include dates in filenames

3. **Check Existing Tables**
   - Review what's already in database
   - Delete old merge tables if needed
   - Back up important data

### During Merge

1. **Be Patient**
   - Large datasets take time
   - 100MB+ files may take 5-10 minutes
   - Check backend console for progress

2. **Monitor Status**
   - Watch status messages
   - Check for error notifications
   - Backend console shows details

### After Merge

1. **Verify Results**
   - Check row count matches expectations
   - Browse the merged table
   - Test Global Search

2. **Clean Up** (Optional)
   - Delete individual tables if not needed
   - Keep `merged_all_data` table
   - Archive original files

---

## 🚦 Performance

### Speed Estimates

**Small Dataset** (< 50MB, < 100K rows):
- Processing: 30 seconds - 2 minutes
- 5-10 files: ~1 minute

**Medium Dataset** (50-500MB, 100K-1M rows):
- Processing: 2-10 minutes
- 10-20 files: ~5 minutes

**Large Dataset** (500MB+, 1M+ rows):
- Processing: 10-30 minutes
- 20+ files: ~15-20 minutes

**Factors Affecting Speed:**
- Number of files
- Total file size
- Number of columns
- Excel vs CSV (CSV is faster)
- System RAM and CPU

---

## 🐛 Troubleshooting

### Common Issues

**1. "No data found to merge"**
- **Cause**: No files in folders, no existing tables
- **Fix**: Upload files or add them to data folder

**2. "Some files had errors"**
- **Cause**: Corrupted files, unsupported format, encoding issues
- **Fix**: Check error list, fix problematic files, re-merge

**3. Merge takes too long**
- **Cause**: Very large datasets
- **Fix**: Be patient, check backend console for progress

**4. "Error creating merged table"**
- **Cause**: Memory issues, column conflicts
- **Fix**: Try merging fewer files at once

**5. Table not showing after merge**
- **Cause**: Merge failed silently
- **Fix**: Check backend console, click "Refresh Tables"

### Error Messages

**File-Level Errors:**
```
"file.xlsx: No module named 'openpyxl'"
```
Fix: File format issue, skip and continue

**Connection Errors:**
```
"Connection error. Check if backend is running."
```
Fix: Ensure backend is on port 8000

**Data Errors:**
```
"Error combining data: cannot concatenate"
```
Fix: Column type mismatch, may need data cleaning

---

## 📈 Advanced Usage

### Merge Strategy: Incremental Updates

1. **Initial Merge**: Merge all historical data
2. **Add New Data**: Upload new files
3. **Re-Merge**: Click Merge All Data again
4. **Result**: Updated master table with all data

### Using Metadata Columns

**Filter by Source:**
```sql
SELECT * FROM merged_all_data 
WHERE _source_file = 'sales_2024.xlsx'
```

**Find Data from Specific Folder:**
```sql
SELECT * FROM merged_all_data 
WHERE _source_folder = 'uploads'
```

**Check File Types:**
```sql
SELECT _file_type, COUNT(*) 
FROM merged_all_data 
GROUP BY _file_type
```

### Combining with Global Search

**Power Workflow:**
1. Merge All Data → creates `merged_all_data`
2. Browse → select `merged_all_data`
3. Search → find anything across all sources!

**Example Searches:**
- "2024" - All 2024 records from any file
- "customer@email.com" - Customer across all datasets
- "Pending" - All pending items from any source
- "INV-12345" - Invoice from any file/table

---

## 🎯 Comparison: Merge Types

### Merge Excel Files

**What it does:**
- Merges only Excel files (.xlsx, .xls)
- From data folder only
- Creates `merged_excel_data` table

**Use when:**
- You only have Excel files
- Files are in data folder
- Quick Excel-only merge needed

### Merge All Data

**What it does:**
- Merges ALL file types (CSV, Excel, TXT)
- From data folder AND uploads folder
- Includes existing database tables
- Creates `merged_all_data` table

**Use when:**
- You have mixed file types
- Files in multiple locations
- Want to include existing tables
- Need complete consolidation

---

## 📚 Example Workflows

### Workflow 1: Year-End Report

```
Goal: Create master dataset for annual analysis

Steps:
1. Place Q1-Q4 reports in data folder
2. Upload any CSV exports to uploads
3. Click "Merge All Data"
4. Browse merged_all_data table
5. Search for specific metrics
6. Export for reporting
```

### Workflow 2: Customer 360 View

```
Goal: Combine all customer touchpoints

Data Sources:
- customer_profiles.csv
- order_history.xlsx
- support_tickets.txt
- website_analytics.csv

Steps:
1. Upload all files
2. Merge All Data
3. Search by customer ID or email
4. View complete customer history
```

### Workflow 3: Multi-Department Data

```
Goal: Consolidate data from different teams

Sources:
- Sales team: sales_data.xlsx (uploads)
- Marketing: campaign_results.csv (data folder)
- Operations: inventory.xlsx (data folder)
- Finance: expenses.csv (uploads)

Steps:
1. Each team uploads their data
2. Add any folder files
3. Merge All Data once
4. Everyone searches same master table
```

---

## 🔐 Data Safety

### What Happens to Original Data?

✅ **Original files**: Untouched, remain in folders  
✅ **Individual tables**: Preserved, not deleted  
✅ **merged_all_data**: New table created  
✅ **Previous merges**: Overwritten (old `merged_all_data` replaced)  

### Backup Recommendation

Before large merges:
```powershell
# Backup database
Copy-Item gigasheet_persistent.db gigasheet_backup.db
```

Or use built-in backup:
- Go to Analyze tab → Use backup endpoint
- Creates timestamped backup file

---

## 🆚 Before vs After

### Before Merge All Data

❌ **Scattered Data**
- 10 separate tables
- Multiple file locations
- Need to search each one
- Time-consuming analysis

❌ **Limited Search**
- Search one table at a time
- Miss data in other files
- Manual consolidation needed

### After Merge All Data

✅ **Unified Data**
- 1 master table
- All data in one place
- Single source of truth
- Complete visibility

✅ **Powerful Search**
- Search across everything
- Find data anywhere
- Instant results
- Complete insights

---

## 📞 Getting Help

### Documentation

- **This Guide**: MERGE_ALL_DATA_GUIDE.md
- **Search Guide**: GLOBAL_SEARCH_GUIDE.md
- **Quick Start**: QUICK_START.md
- **API Docs**: http://localhost:8000/docs

### Support Steps

1. Check backend console for detailed logs
2. Verify files are in correct folders
3. Ensure files are supported formats
4. Try merging fewer files first
5. Check available disk space and RAM

### Common Questions

**Q: How long does it take?**  
A: Depends on data size. 10 files ~2-5 minutes.

**Q: Can I merge again after first time?**  
A: Yes! Re-merging updates the master table.

**Q: Will it delete my original files?**  
A: No! Original files are never touched.

**Q: What if some files fail?**  
A: Merge continues, shows errors after completion.

**Q: How do I know what's in merged table?**  
A: Use `_source_file` column to see where each row came from.

---

## 🎉 Summary

The **Merge All Data** feature is your ultimate data consolidation tool:

✅ **Combines EVERYTHING** - All files, all formats, all tables  
✅ **One Master Table** - Single source of truth  
✅ **Global Search Ready** - Search across all data at once  
✅ **Smart Merging** - Handles different columns automatically  
✅ **Error Resilient** - Continues even if some files fail  
✅ **Metadata Tracking** - Know where each row came from  

**Ready to merge? Go to Upload tab and click "Merge All Data"!**

---

*Last Updated: 2025-10-02*  
*Version 2.1 with Merge All Data + Global Search*
