# Local Gigasheet Clone: Complete Implementation

## Architecture Overview

Our local implementation replicates Gigasheet's core functionality using open-source technologies:

```
CSV Files → DuckDB/ClickHouse → Parquet Storage → React + AG Grid Frontend
```

## Backend Implementation (Python + FastAPI + DuckDB)

### 1. Main Application (app.py)

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd
import os
from typing import Optional, List
import json

app = FastAPI(title="Local Gigasheet Clone")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DuckDB connection
conn = duckdb.connect('gigasheet_local.db')

class DataProcessor:
    def __init__(self):
        self.conn = conn
        
    def csv_to_parquet_and_load(self, csv_path: str, table_name: str):
        """Convert CSV to Parquet and load into DuckDB"""
        print(f"Processing {csv_path}...")
        
        # Create parquet file path
        parquet_path = csv_path.replace('.csv', '.parquet')
        
        # Convert CSV to Parquet using DuckDB (ultra-fast)
        self.conn.execute(f"""
            COPY (SELECT * FROM read_csv_auto('{csv_path}')) 
            TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION snappy)
        """)
        
        # Create table from parquet
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_parquet('{parquet_path}')
        """)
        
        print(f"✅ Created table {table_name} with Parquet backend")
        return parquet_path

    def get_table_info(self, table_name: str):
        """Get table metadata"""
        # Get row count
        row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        # Get column info
        columns = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
        
        return {
            "row_count": row_count,
            "columns": [{"name": col[0], "type": col[1]} for col in columns]
        }

    def get_data_page(self, table_name: str, offset: int = 0, limit: int = 100, 
                      filters: Optional[dict] = None, sort_column: Optional[str] = None, 
                      sort_direction: str = "ASC"):
        """Get paginated data with filters and sorting"""
        
        # Build WHERE clause from filters
        where_clause = ""
        if filters:
            conditions = []
            for column, filter_value in filters.items():
                if filter_value:
                    conditions.append(f"{column} ILIKE '%{filter_value}%'")
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
        
        # Build ORDER BY clause
        order_clause = ""
        if sort_column:
            order_clause = f"ORDER BY {sort_column} {sort_direction}"
        
        # Execute query
        query = f"""
            SELECT * FROM {table_name} 
            {where_clause}
            {order_clause}
            LIMIT {limit} OFFSET {offset}
        """
        
        result = self.conn.execute(query).fetchall()
        columns = [desc[0] for desc in self.conn.description]
        
        # Convert to list of dictionaries
        data = [dict(zip(columns, row)) for row in result]
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
        total_count = self.conn.execute(count_query).fetchone()[0]
        
        return {
            "data": data,
            "total_count": total_count,
            "page_size": limit,
            "current_page": offset // limit + 1
        }

# Initialize processor
processor = DataProcessor()

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process file
    table_name = file.filename.replace('.csv', '').replace('-', '_').replace(' ', '_')
    parquet_path = processor.csv_to_parquet_and_load(file_path, table_name)
    
    # Get table info
    info = processor.get_table_info(table_name)
    
    return {
        "message": "File uploaded successfully",
        "table_name": table_name,
        "parquet_path": parquet_path,
        "info": info
    }

@app.get("/tables")
def list_tables():
    """List all available tables"""
    tables = processor.conn.execute("SHOW TABLES").fetchall()
    return {"tables": [table[0] for table in tables]}

@app.get("/tables/{table_name}/info")
def get_table_info(table_name: str):
    """Get table metadata"""
    return processor.get_table_info(table_name)

@app.get("/tables/{table_name}/data")
def get_table_data(
    table_name: str,
    offset: int = 0,
    limit: int = 100,
    sort_column: Optional[str] = None,
    sort_direction: str = "ASC",
    filters: Optional[str] = None
):
    """Get paginated table data with filtering and sorting"""
    
    # Parse filters from JSON string
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except:
            pass
    
    return processor.get_data_page(
        table_name, offset, limit, filter_dict, sort_column, sort_direction
    )

@app.post("/merge-excel-files")
async def merge_excel_files():
    """Merge multiple Excel files into a single table"""
    # This endpoint would handle your 10 Excel files
    excel_folder = "excel_files"  # Update path
    
    if not os.path.exists(excel_folder):
        raise HTTPException(status_code=404, detail="Excel folder not found")
    
    excel_files = [f for f in os.listdir(excel_folder) if f.endswith(('.xlsx', '.xls'))]
    
    # Create merged table
    processor.conn.execute("DROP TABLE IF EXISTS merged_excel_data")
    
    for i, file in enumerate(excel_files):
        file_path = os.path.join(excel_folder, file)
        
        if i == 0:
            # Create table from first file
            processor.conn.execute(f"""
                CREATE TABLE merged_excel_data AS 
                SELECT *, '{file}' as source_file FROM read_excel('{file_path}')
            """)
        else:
            # Insert from subsequent files
            processor.conn.execute(f"""
                INSERT INTO merged_excel_data 
                SELECT *, '{file}' as source_file FROM read_excel('{file_path}')
            """)
    
    # Convert to Parquet for better performance
    processor.conn.execute("""
        COPY merged_excel_data TO 'merged_excel_data.parquet' 
        (FORMAT PARQUET, COMPRESSION snappy)
    """)
    
    info = processor.get_table_info("merged_excel_data")
    
    return {
        "message": f"Successfully merged {len(excel_files)} Excel files",
        "table_name": "merged_excel_data",
        "files_processed": excel_files,
        "info": info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Requirements (requirements.txt)

```
fastapi==0.104.1
uvicorn==0.24.0
duckdb==0.9.2
pandas==2.1.4
python-multipart==0.0.6
openpyxl==3.1.2
```

### 3. Alternative ClickHouse Implementation (clickhouse_app.py)

```python
import clickhouse_connect
from fastapi import FastAPI
import pandas as pd

class ClickHouseProcessor:
    def __init__(self):
        # For local ClickHouse, use clickhouse-local
        self.client = clickhouse_connect.get_client(
            host='localhost',
            port=8123,
            username='default'
        )
    
    def csv_to_clickhouse(self, csv_path: str, table_name: str):
        """Load CSV into ClickHouse with automatic schema detection"""
        
        # Read CSV with pandas to infer schema
        df = pd.read_csv(csv_path, nrows=1000)  # Sample for schema
        
        # Create ClickHouse table
        create_table_sql = self.generate_create_table_sql(df, table_name)
        self.client.command(create_table_sql)
        
        # Insert data using ClickHouse's CSV format
        with open(csv_path, 'r') as f:
            self.client.raw_insert(
                f"INSERT INTO {table_name} FORMAT CSV",
                f.read().encode()
            )
    
    def generate_create_table_sql(self, df: pd.DataFrame, table_name: str) -> str:
        """Generate CREATE TABLE SQL from pandas DataFrame"""
        type_mapping = {
            'object': 'String',
            'int64': 'Int64',
            'float64': 'Float64',
            'bool': 'Bool',
            'datetime64[ns]': 'DateTime'
        }
        
        columns = []
        for col, dtype in df.dtypes.items():
            ch_type = type_mapping.get(str(dtype), 'String')
            columns.append(f"`{col}` {ch_type}")
        
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns)}
        ) ENGINE = MergeTree()
        ORDER BY tuple()
        """
```

## Frontend Implementation (React + AG Grid)

### 1. Package.json

```json
{
  "name": "gigasheet-clone-frontend",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "ag-grid-react": "^31.0.3",
    "ag-grid-community": "^31.0.3",
    "ag-grid-enterprise": "^31.0.3",
    "axios": "^1.6.2",
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
```

### 2. Main Component (App.js)

```javascript
import React, { useState, useEffect, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [rowData, setRowData] = useState([]);
  const [columnDefs, setColumnDefs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentTable, setCurrentTable] = useState('');
  const [totalRows, setTotalRows] = useState(0);
  const [tables, setTables] = useState([]);

  // AG Grid pagination and filtering
  const [filterModel, setFilterModel] = useState({});
  const [sortModel, setSortModel] = useState([]);

  // Load available tables
  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tables`);
      setTables(response.data.tables);
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  };

  const loadTableData = async (tableName, offset = 0, limit = 100) => {
    setLoading(true);
    try {
      // Build filter parameters
      const filterParams = Object.keys(filterModel).length > 0 
        ? `&filters=${encodeURIComponent(JSON.stringify(filterModel))}`
        : '';
      
      // Build sort parameters
      const sortParams = sortModel.length > 0
        ? `&sort_column=${sortModel[0].colId}&sort_direction=${sortModel[0].sort.toUpperCase()}`
        : '';

      const response = await axios.get(
        `${API_BASE_URL}/tables/${tableName}/data?offset=${offset}&limit=${limit}${filterParams}${sortParams}`
      );

      const data = response.data;
      setRowData(data.data);
      setTotalRows(data.total_count);

      // Setup column definitions
      if (data.data.length > 0) {
        const columns = Object.keys(data.data[0]).map(key => ({
          headerName: key,
          field: key,
          sortable: true,
          filter: true,
          resizable: true,
          minWidth: 150
        }));
        setColumnDefs(columns);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert(`File uploaded successfully! Table: ${response.data.table_name}`);
      fetchTables();
      setCurrentTable(response.data.table_name);
      loadTableData(response.data.table_name);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file');
    }
    setLoading(false);
  };

  // Handle Excel merge
  const handleExcelMerge = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/merge-excel-files`);
      alert(response.data.message);
      fetchTables();
      setCurrentTable('merged_excel_data');
      loadTableData('merged_excel_data');
    } catch (error) {
      console.error('Error merging Excel files:', error);
      alert('Error merging Excel files');
    }
    setLoading(false);
  };

  // AG Grid event handlers
  const onFilterChanged = (params) => {
    const newFilterModel = params.api.getFilterModel();
    setFilterModel(newFilterModel);
    // Reload data with new filters
    loadTableData(currentTable, 0, 100);
  };

  const onSortChanged = (params) => {
    const newSortModel = params.api.getSortModel();
    setSortModel(newSortModel);
    // Reload data with new sorting
    loadTableData(currentTable, 0, 100);
  };

  // Grid options for performance
  const gridOptions = {
    defaultColDef: {
      sortable: true,
      filter: true,
      resizable: true,
      minWidth: 100
    },
    rowModelType: 'serverSide',
    cacheBlockSize: 100,
    maxBlocksInCache: 10,
    animateRows: true,
    enableRangeSelection: true,
    suppressRowClickSelection: true,
    pagination: true,
    paginationPageSize: 100
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>🚀 Local Gigasheet Clone</h1>
      
      {/* Upload Section */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          disabled={loading}
        />
        <button 
          onClick={handleExcelMerge}
          disabled={loading}
          style={{ marginLeft: '10px' }}
        >
          Merge Excel Files
        </button>
      </div>

      {/* Table Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label>Select Table: </label>
        <select 
          value={currentTable} 
          onChange={(e) => {
            setCurrentTable(e.target.value);
            loadTableData(e.target.value);
          }}
        >
          <option value="">-- Select Table --</option>
          {tables.map(table => (
            <option key={table} value={table}>{table}</option>
          ))}
        </select>
        {totalRows > 0 && (
          <span style={{ marginLeft: '10px' }}>
            Total Rows: {totalRows.toLocaleString()}
          </span>
        )}
      </div>

      {/* Data Grid */}
      <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          gridOptions={gridOptions}
          loading={loading}
          onFilterChanged={onFilterChanged}
          onSortChanged={onSortChanged}
        />
      </div>
    </div>
  );
}

export default App;
```

## Deployment Instructions

### 1. Backend Setup

```bash
# Create project directory
mkdir gigasheet-clone && cd gigasheet-clone

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir uploads excel_files

# Run backend
python app.py
```

### 2. Frontend Setup

```bash
# In new terminal, create React app
npx create-react-app frontend
cd frontend

# Install AG Grid and dependencies
npm install ag-grid-react ag-grid-community ag-grid-enterprise axios

# Replace src/App.js with our implementation
# Run frontend
npm start
```

### 3. Performance Optimizations

1. **DuckDB Configuration**:
   - Enable parallel processing
   - Optimize memory settings
   - Use Parquet for storage

2. **Frontend Optimizations**:
   - Virtual scrolling with AG Grid
   - Server-side pagination
   - Debounced filtering
   - Column virtualization

3. **File Processing**:
   - Stream processing for large files
   - Chunked uploads
   - Background processing

This implementation provides Gigasheet-like functionality locally with excellent performance for your 1 crore row dataset!