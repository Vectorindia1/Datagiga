# 🚀 Data Studio - Quick Start Guide

## Starting the Application

### Option 1: Automated Start (Recommended)
```powershell
.\START_DATA_STUDIO.ps1
```

This will:
- ✅ Check if Python is installed
- ✅ Start backend server (port 8000)
- ✅ Start frontend server (port 3000)
- ✅ Open browser automatically

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd gigasheet-local\backend
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
python server.py
```

---

## Using Data Studio

### 📱 Accessing the Interface

Once started, open your browser to:
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🎯 Features Overview

### 1️⃣ Upload Tab

**Upload CSV/Excel Files:**
1. Click the upload area OR drag & drop files
2. Supported formats: `.csv`, `.xlsx`, `.xls`, `.txt`
3. File info will display after selection
4. Click "Upload & Process" to process

**Merge Excel Files:**
1. Place all Excel files in `gigasheet-local/data/` directory
2. Click "Merge Excel Files" button
3. Wait for processing (may take minutes for large files)
4. Merged table will be available in Browse tab

---

### 2️⃣ Browse Tab

**View Your Data:**
1. Select a table from the dropdown
2. Data preview loads automatically
3. See statistics: total rows, columns
4. First 50 rows displayed for quick preview

**Refresh Tables:**
- Click "Refresh Tables" to update the list after uploading

---

### 3️⃣ Analyze Tab

**System Monitoring:**
- Backend Status: Online/Offline indicator
- Total Tables: Number of tables in database
- Total Rows: Combined rows across all tables

**Links:**
- "Refresh Status": Update statistics
- "API Docs": View FastAPI documentation

---

## 💡 Quick Tips

### File Upload
- ✅ **Drag & Drop**: Fastest method - just drop files
- ✅ **Size Indicator**: Shows file size after selection
- ✅ **Large Files**: Be patient, 100MB+ files take time
- ⚠️ **Backend Must Be Running**: Upload won't work otherwise

### Data Browsing
- 📊 **Preview Only**: Currently shows first 50 rows
- 🔄 **Refresh**: Click refresh if table list doesn't update
- 📈 **Large Datasets**: Backend handles millions of rows efficiently

### Performance
- ⚡ **DuckDB**: Optimized for 32GB RAM systems
- 💾 **Persistent Storage**: Data saved in `gigasheet_persistent.db`
- 🚀 **Fast Queries**: Sub-second filtering on 10M+ rows

---

## 🎨 UI Elements Explained

### Color Indicators

**🔵 Cyan (#4facfe)**
- Primary action buttons
- Active tab indicator
- Important stats/numbers
- Hover effects

**🟢 Green (#43e97b)**
- Success messages
- Positive indicators

**🔴 Red (#ff6b6b)**
- Error messages
- Failed operations

**⚪ Gray Tones**
- Normal text and UI elements
- Secondary buttons

---

## 🔧 Troubleshooting

### "Backend is Offline" Message
```powershell
# Make sure backend is running:
cd gigasheet-local\backend
python main.py
```

### "Port Already in Use"
```powershell
# Kill existing process:
Stop-Process -Name python -Force

# Or change ports in:
# - frontend/server.py (PORT = 3000)
# - backend/main.py (port = 8000)
```

### Files Not Uploading
- ✅ Check backend is running (green status)
- ✅ Verify file format (CSV, XLSX, XLS)
- ✅ Check console for error messages
- ✅ Ensure file isn't locked by another program

### Tables Not Showing
- Click "Refresh Tables" button
- Check backend console for errors
- Verify upload completed successfully

### Slow Performance
- Close unnecessary applications
- Check available RAM (system optimized for 32GB)
- Large files (1GB+) naturally take longer

---

## 📂 File Locations

```
GigaSheet/
├── frontend/
│   ├── index.html          ← Main UI file (redesigned)
│   └── server.py           ← Frontend server
│
├── gigasheet-local/
│   ├── backend/
│   │   └── main.py         ← Backend API
│   └── data/               ← PUT YOUR EXCEL FILES HERE
│
├── uploads/                ← Uploaded CSV files stored here
├── gigasheet_persistent.db ← Database file (persistent)
└── START_DATA_STUDIO.ps1   ← Quick start script
```

---

## 🎯 Common Workflows

### Workflow 1: Upload & View CSV
```
1. Go to "Upload" tab
2. Drag & drop your CSV file
3. Click "Upload & Process"
4. Switch to "Browse" tab
5. Select your table from dropdown
6. View your data!
```

### Workflow 2: Merge Multiple Excel Files
```
1. Copy Excel files to gigasheet-local/data/
2. Go to "Upload" tab
3. Click "Merge Excel Files"
4. Wait for processing
5. Switch to "Browse" tab
6. Select "merged_excel_data" table
7. Your merged data is ready!
```

### Workflow 3: Monitor System
```
1. Go to "Analyze" tab
2. View backend status
3. Check total tables/rows
4. Click "Refresh Status" for updates
5. Click "API Docs" to explore backend
```

---

## 🆘 Getting Help

### Check Logs

**Backend Console:**
- Shows processing status
- Displays errors and warnings
- Tracks file operations

**Frontend Console:**
- Network errors
- API connection issues
- JavaScript errors (F12 in browser)

### Common Issues

**Issue:** "No tables found"
- **Fix:** Upload a file first, or check if database file exists

**Issue:** "Upload failed"
- **Fix:** Check file format, size, and backend status

**Issue:** "Connection refused"
- **Fix:** Ensure backend is running on port 8000

**Issue:** "Browser not opening"
- **Fix:** Manually navigate to http://localhost:3000

---

## ⚙️ Configuration

### Backend Settings

Edit `gigasheet-local/backend/main.py`:

```python
# Database configuration
DB_FILE = 'gigasheet_persistent.db'

# Performance tuning
config={
    'threads': 16,              # Adjust based on CPU cores
    'memory_limit': '24GB',     # Adjust based on RAM
    'max_memory': '28GB',       # Peak usage limit
}

# CORS (if accessing from different domain)
allow_origins=["*"]  # Change to specific origins for security
```

### Frontend Settings

Edit `frontend/server.py`:

```python
PORT = 3000  # Change frontend port
```

---

## 📊 Data Formats

### Supported Input Formats
- **CSV** (`.csv`): Comma-separated values
- **Excel** (`.xlsx`, `.xls`): Microsoft Excel
- **Text** (`.txt`): Tab or comma delimited

### Export Formats
Use backend API to export:
- CSV
- Parquet
- Excel

---

## 🎉 You're All Set!

Your Data Studio is ready to handle massive datasets with style. The modern dark interface makes working with data a pleasant experience.

**Enjoy your new data analysis tool!** 🚀

---

## 📚 Additional Resources

- `FRONTEND_REDESIGN.md` - Detailed feature documentation
- `DESIGN_CHANGES.md` - Visual design comparison
- http://localhost:8000/docs - Interactive API documentation

---

**Questions?** Check the backend console for detailed logs and error messages.
