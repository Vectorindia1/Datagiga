# 🚀 GigaSheet Features - Quick Reference Card

## 🎯 Core Features

### 1. 📤 Upload Data
**Location:** Upload Tab

- **Single File Upload**: Drag & drop or click to select
- **Supported Formats**: CSV, Excel (.xlsx, .xls), TXT
- **Auto-Processing**: Creates individual tables automatically

### 2. 🔗 Merge Excel Files  
**Location:** Upload Tab

- **What**: Merges all Excel files from data folder
- **Result**: Creates `merged_excel_data` table
- **Use For**: Excel-only consolidation

### 3. 🔗 Merge ALL Data (NEW!)
**Location:** Upload Tab (highlighted card)

- **What**: Combines EVERYTHING - CSV, Excel, TXT, all sources
- **Sources**: 
  - Data folder (`gigasheet-local/data/`)
  - Uploads folder
  - Existing database tables
- **Result**: Creates `merged_all_data` master table
- **Metadata**: Adds `_source_file`, `_source_folder`, `_file_type`

### 4. 🔍 Global Search (NEW!)
**Location:** Browse Tab (after selecting table)

- **What**: Search across ALL columns in any table
- **Features**:
  - Case-insensitive
  - Partial matching
  - Shows match count
  - Works with merged data
- **Use**: Find anything across all your data instantly

### 5. 📊 Browse Data
**Location:** Browse Tab

- **What**: View and explore table data
- **Features**:
  - Table selection dropdown
  - Data preview (first 50 rows)
  - Statistics display
  - Integrated search

### 6. 📈 Analyze System
**Location:** Analyze Tab

- **What**: Monitor system health and database stats
- **Shows**:
  - Backend status (online/offline)
  - Total tables count
  - Total rows across all tables
  - Refresh capability

---

## 🎬 Quick Workflows

### Workflow A: Upload & Search Single File
```
1. Upload Tab → Select file → Upload & Process
2. Browse Tab → Select table
3. Enter search query → Press Enter
4. View results
```
**Time**: 1-2 minutes

### Workflow B: Merge Multiple Excel Files
```
1. Place Excel files in gigasheet-local/data/
2. Upload Tab → Click "Merge Excel Files"
3. Wait for processing
4. Browse Tab → Select "merged_excel_data"
5. Search across all merged data
```
**Time**: 2-5 minutes

### Workflow C: Merge EVERYTHING & Search (Recommended!)
```
1. Upload files via UI OR place in data folder
2. Upload Tab → Click "Merge All Data"
3. Wait for processing (shows stats)
4. Browse Tab → Select "merged_all_data"
5. Search for ANYTHING across ALL data!
```
**Time**: 3-10 minutes (depending on data size)

---

## 🎯 When to Use What?

### Use **Single Upload** when:
- ✅ You have one file to analyze
- ✅ Quick data preview needed
- ✅ File is small (< 10MB)

### Use **Merge Excel Files** when:
- ✅ You only have Excel files
- ✅ All files are in data folder
- ✅ Need Excel-specific merge

### Use **Merge All Data** when:
- ✅ You have mixed file types (CSV, Excel, TXT)
- ✅ Files in multiple locations
- ✅ Want to include existing tables
- ✅ Need complete consolidation
- ✅ **Want to search across EVERYTHING**

---

## 🔍 Search Tips

### What You Can Search:
- **Names**: "John Smith", "ProductX"
- **Numbers**: Invoice IDs, amounts, quantities
- **Dates**: "2024", "2024-03", "2024-03-15"
- **Emails**: "user@domain.com", "@gmail.com"
- **Status**: "pending", "completed", "active"
- **Codes**: "INV-12345", "ORD-5678"
- **Anything**: Literally any text or number in your data

### Search Best Practices:
1. **Start Broad**: "john" → then narrow "john smith"
2. **Use Unique IDs**: Invoice numbers, order IDs
3. **Partial Works**: "tech" finds "technology", "technical"
4. **Case Doesn't Matter**: "JOHN" = "john" = "John"

---

## 📊 Understanding Metadata Columns

After merging all data, you'll see special columns:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `_source_file` | Original filename | `sales_2024.xlsx` |
| `_source_folder` | Where it came from | `data folder`, `uploads`, `database` |
| `_file_type` | File extension | `.xlsx`, `.csv`, `.txt`, `.table` |

**Use metadata to:**
- Filter by source file
- Identify data origin
- Track data lineage

---

## 🚀 Power User Shortcuts

### Keyboard Shortcuts:
- **Search**: Press `Enter` in search box
- **Clear Search**: Click Clear button

### Fastest Workflow:
```
Upload → Merge All → Search → Find Anything
(One search finds data across ALL files!)
```

### Pro Tips:
1. **Merge Once, Search Forever**: After merging, search repeatedly without re-merging
2. **Use Metadata**: Search `_source_file` column to find which file has data
3. **Incremental Updates**: Re-merge after adding new files to update master table
4. **Name Files Well**: Use descriptive names with dates (sales_2024_q1.xlsx)

---

## 📱 UI Navigation

### Tab Layout:
```
[Upload] [Browse] [Analyze]
   ↓        ↓         ↓
 Add     View &    System
 Data    Search    Stats
```

### Upload Tab Cards:
1. **Upload files** - Single file upload
2. **Merge Excel Files** - Excel-only merge
3. **Merge ALL Data** (Blue Border) - Complete merge ⭐

### Browse Tab Cards:
1. **Available Tables** - Table selection
2. **Search Data** - Global search (appears after selecting table) ⭐
3. **Data Preview** - Table display

---

## 🎨 Visual Indicators

### Status Colors:
- 🟢 **Green**: Success, online, completed
- 🔵 **Blue**: Info, processing, active
- 🔴 **Red**: Error, offline, failed
- 🟡 **Yellow**: Warning, attention needed

### Button Types:
- **Blue Gradient Button**: Primary action (Merge All Data)
- **Blue Button**: Regular action (Search, Upload)
- **Gray Button**: Secondary action (Clear, Refresh)

---

## 📈 Performance Guidelines

### File Size Limits:
- **Small** (< 50MB): Very fast, < 1 min
- **Medium** (50-500MB): Fast, 2-5 mins
- **Large** (500MB+): Slower, 5-15 mins
- **Very Large** (1GB+): Patience needed, 15-30 mins

### Optimization Tips:
- CSV is faster than Excel
- Close other applications during merge
- Monitor backend console for progress
- System optimized for 32GB RAM

---

## 🐛 Quick Troubleshooting

### "Backend is Offline"
**Fix**: Check if backend running on port 8000

### "No results found"
**Fix**: Try broader search terms, check spelling

### "No data found to merge"
**Fix**: Upload files or add to data folder first

### "Search not working"
**Fix**: Ensure table is selected in dropdown

### Merge taking too long
**Fix**: Be patient, check backend console for progress

---

## 📚 Documentation Index

- **QUICK_START.md** - Getting started guide
- **GLOBAL_SEARCH_GUIDE.md** - Complete search documentation
- **MERGE_ALL_DATA_GUIDE.md** - Complete merge documentation
- **HOW_TO_START_WITH_SEARCH.md** - Quick start reference
- **FEATURES_QUICK_REFERENCE.md** - This file

---

## 🌐 URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend UI | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Interactive API documentation |

---

## ⚡ Common Commands

### Start Application:
```powershell
.\start-simple.ps1
```

### Stop Services:
```powershell
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### Check Status:
```powershell
Get-Job
```

---

## 🎯 Feature Comparison Table

| Feature | Single Upload | Merge Excel | Merge All Data |
|---------|--------------|-------------|----------------|
| **File Types** | One file | Excel only | ALL types |
| **Sources** | Upload only | Data folder | Everywhere |
| **Table Count** | 1 per file | 1 merged | 1 master |
| **Speed** | Fastest | Fast | Depends |
| **Use Case** | Quick view | Excel merge | **Complete consolidation** ⭐ |
| **Search** | Per table | Merged data | **ALL data** ⭐ |

---

## 💡 Key Insights

### The Power Combination:
```
Merge All Data + Global Search = 🔥 ULTIMATE DATA TOOL
```

**Why?**
- ✅ All your data in one place
- ✅ Search across everything instantly
- ✅ No file switching needed
- ✅ Complete data visibility
- ✅ Find anything anywhere

### Best Practices Summary:
1. **Upload early, merge often**
2. **Use descriptive filenames**
3. **Merge all data for best search results**
4. **Check backend console for details**
5. **Refresh tables after operations**

---

## 🎉 Quick Start Checklist

- [ ] Start application (`.\start-simple.ps1`)
- [ ] Upload or add files to data folder
- [ ] Click "Merge All Data" in Upload tab
- [ ] Wait for processing to complete
- [ ] Go to Browse tab
- [ ] Select "merged_all_data" table
- [ ] Enter search query
- [ ] **Find anything across all your data!** 🚀

---

## 📞 Need Help?

1. Check documentation files
2. Visit http://localhost:8000/docs
3. Check backend console logs
4. Verify services are running
5. Refresh browser if needed

---

**Version**: 2.1 with Merge All Data + Global Search  
**Last Updated**: 2025-10-02

**🎊 Congratulations! You now have a powerful data consolidation and search tool!**
