# 🚀 How to Start GigaSheet with Global Search

## Quick Start

### Option 1: Automated Start (Recommended)

Open PowerShell in the project directory and run:

```powershell
.\start-simple.ps1
```

This will:
- Start backend server (port 8000)
- Start frontend server (port 3000)
- Open browser automatically

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd gigasheet-local\backend
..\..\..venv\Scripts\Activate.ps1
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
..\.venv\Scripts\Activate.ps1
python server.py
```

---

## Stopping the Services

If services are running as background jobs:

```powershell
# Stop backend
Stop-Job -Id <backend_job_id>
Remove-Job -Id <backend_job_id>

# Or stop all Python processes
Stop-Process -Name python -Force
```

---

## Accessing the Application

Once started, access these URLs:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## Using Global Search

### Step-by-Step:

1. **Upload or Merge Data**
   - Go to Upload tab
   - Upload CSV/Excel files OR
   - Click "Merge Excel Files" to combine multiple files

2. **Browse and Search**
   - Go to Browse tab
   - Select a table from dropdown
   - Search box appears automatically

3. **Search Your Data**
   - Type anything: names, numbers, dates, codes
   - Press Enter or click Search
   - See results instantly across ALL columns!

4. **Clear and Repeat**
   - Click Clear to return to full table
   - Try different search terms

---

## Features Available

✅ **Upload Tab**
- Single file upload (CSV, Excel, TXT)
- Multiple file merge
- Drag & drop support

✅ **Browse Tab**
- Table selection
- Data preview
- **🔍 GLOBAL SEARCH** - NEW!
- Search across all columns
- Real-time results

✅ **Analyze Tab**
- System status
- Table statistics
- Backend health check

---

## Global Search Capabilities

### What You Can Search:

- **Text**: Customer names, descriptions, notes
- **Numbers**: IDs, amounts, quantities
- **Dates**: Any date format (2024-03-15, March 2024, etc.)
- **Codes**: Invoice numbers, product codes, SKUs
- **Emails**: Search by domain or name
- **Anything**: Literally any value in your data!

### Search Features:

- ✅ Case-insensitive
- ✅ Partial matching
- ✅ All columns automatically
- ✅ Fast results (seconds)
- ✅ Shows match count
- ✅ Works with merged data

---

## Example Workflows

### Workflow 1: Search Uploaded CSV

```
1. Upload → customers.csv
2. Browse → Select "customers"
3. Search → "john"
4. Results → All rows containing "john" anywhere
```

### Workflow 2: Search Merged Excel Files

```
1. Place files in gigasheet-local/data/:
   - sales_2023.xlsx
   - sales_2024.xlsx
   - inventory.xlsx

2. Upload → Click "Merge Excel Files"

3. Browse → Select "merged_excel_data"

4. Search → "2024" or "ProductX" or "pending"

5. Results → Matches from ALL files combined!
```

---

## Troubleshooting

### Backend Won't Start

```powershell
# Check if port 8000 is in use
Get-NetTCPConnection -LocalPort 8000

# Kill process if needed
Stop-Process -Name python -Force
```

### Frontend Won't Start

```powershell
# Check if port 3000 is in use
Get-NetTCPConnection -LocalPort 3000

# Kill process if needed
Stop-Process -Id <process_id> -Force
```

### Search Not Working

1. Make sure a table is selected
2. Verify backend is running (check http://localhost:8000)
3. Try refreshing the page
4. Check browser console for errors (F12)

---

## File Locations

```
GigaSheet/
├── frontend/
│   ├── index.html          # Main UI (with search feature)
│   └── server.py           # Frontend server
│
├── gigasheet-local/
│   ├── backend/
│   │   └── main.py         # Backend API (with search endpoint)
│   └── data/               # Place Excel files here for merge
│
├── uploads/                # Uploaded files stored here
├── gigasheet_persistent.db # Your data (persistent)
├── GLOBAL_SEARCH_GUIDE.md  # Complete search documentation
└── HOW_TO_START_WITH_SEARCH.md # This file
```

---

## Performance Tips

### For Large Datasets:

1. **Be Specific**: "john.smith@company.com" vs just "john"
2. **Use Unique IDs**: Invoice numbers, order IDs, etc.
3. **Limit Results**: Default is 100, max is 1000
4. **Patience**: 10M+ rows may take 10-15 seconds

### For Best Results:

1. **Merge First**: Combine all files before searching
2. **Clean Data**: Consistent formats help find matches
3. **Use Wildcards**: Partial terms work great ("tech" finds "technology")
4. **Clear Between**: Click Clear before new searches

---

## API Usage

### Search Endpoint

```
GET /tables/{table_name}/search?query={search_term}
```

**Example:**
```
http://localhost:8000/tables/customers/search?query=john&limit=50
```

**Response:**
```json
{
  "query": "john",
  "table_name": "customers",
  "total_matches": 150,
  "returned_count": 50,
  "data": [...],
  "columns": [...]
}
```

---

## What's New in This Version

### Backend Changes:

✅ New endpoint: `/tables/{table_name}/search`  
✅ Multi-column search logic  
✅ Optimized SQL queries with ILIKE  
✅ Case-insensitive matching  
✅ Safety against SQL injection  

### Frontend Changes:

✅ Search card in Browse tab  
✅ Real-time search functionality  
✅ Match count display  
✅ Clear search feature  
✅ Search state management  
✅ Visual feedback for results  

### Features:

✅ Search all columns at once  
✅ Works with merged data  
✅ Fast query execution  
✅ Clean UI integration  
✅ Error handling  

---

## Getting Help

### Documentation:

- **Quick Start**: QUICK_START.md
- **Search Guide**: GLOBAL_SEARCH_GUIDE.md
- **API Docs**: http://localhost:8000/docs
- **This Guide**: HOW_TO_START_WITH_SEARCH.md

### Support:

1. Check backend console for errors
2. View browser console (F12) for frontend issues
3. Verify both services are running
4. Try the API docs for testing

---

## Common Commands

### Start Services:
```powershell
.\start-simple.ps1
```

### Stop Services:
```powershell
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### Restart Backend Only:
```powershell
Stop-Job -Id <backend_job_id>
Remove-Job -Id <backend_job_id>
cd gigasheet-local\backend
python main.py
```

### Check Service Status:
```powershell
Get-Job
Get-NetTCPConnection -LocalPort 8000
Get-NetTCPConnection -LocalPort 3000
```

---

## Tips for Success

1. **Start Fresh**: Always use the automated start script
2. **Wait for Startup**: Give servers 5-10 seconds to initialize
3. **Check Status**: Use Analyze tab to verify backend is online
4. **Merge Smart**: Combine related files for powerful searching
5. **Search Often**: The more you use it, the more insights you'll find!

---

## Next Steps

1. ✅ Start the application
2. ✅ Upload or merge your data
3. ✅ Try the global search feature
4. ✅ Explore your data easily
5. ✅ Discover insights quickly!

---

**Happy Searching! 🔍**

*Version 2.1 with Global Search*  
*Last Updated: 2025-10-02*
