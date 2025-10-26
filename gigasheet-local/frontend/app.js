// Minimalistic DataGiga frontend
const API = 'http://127.0.0.1:8000';

let currentPage = 0, pageSize = 100, showAll = false;

// DOM utilities
const $ = id => document.getElementById(id);
const log = (elementId, text, clear = false) => {
  const el = $(elementId);
  if (clear) el.textContent = '';
  el.textContent += text + '\n';
  el.scrollTop = el.scrollHeight;
};

// Backend status check
async function checkBackend() {
  try {
    const res = await fetch(API + '/');
    const data = await res.json();
    $('backend-status').className = 'pill pill-green';
    $('backend-status').textContent = 'Online • ' + data.version;
    refreshTables();
  } catch {
    $('backend-status').className = 'pill pill-red';
    $('backend-status').textContent = 'Offline';
  }
}

// Load tables from backend
async function refreshTables() {
  try {
    const res = await fetch(API + '/tables');
    const data = await res.json();
    const select = $('table-select');
    select.innerHTML = '<option value="">Select table…</option>';
    data.tables.forEach(table => {
      const opt = document.createElement('option');
      opt.value = table;
      opt.textContent = table;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error('Failed to load tables:', err);
  }
}

// File upload
async function uploadFile() {
  const fileInput = $('file-input');
  const file = fileInput.files[0];
  if (!file) return;
  
  log('upload-log', 'Uploading ' + file.name + '...', true);
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const res = await fetch(API + '/upload', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    
    if (result.success) {
      log('upload-log', `✓ Success: ${result.row_count} rows in ${result.table_name}`);
      refreshTables();
    } else {
      log('upload-log', '✗ Upload failed');
    }
  } catch (err) {
    log('upload-log', '✗ Error: ' + err.message);
  }
}

// Merge all data
async function mergeAllData() {
  log('merge-log', 'Starting merge of all data sources...', true);
  
  try {
    const res = await fetch(API + '/merge-all-data', {
      method: 'POST'
    });
    const result = await res.json();
    
    log('merge-log', `✓ ${result.message}`);
    log('merge-log', `Table: ${result.table_name}`);
    log('merge-log', `Total rows: ${result.total_rows?.toLocaleString() || 'N/A'}`);
    log('merge-log', `Files processed: ${result.files_processed?.length || 0}`);
    
    refreshTables();
  } catch (err) {
    log('merge-log', '✗ Merge failed: ' + err.message);
  }
}

// Load/search data
async function loadData(isSearch = false) {
  const table = $('table-select').value;
  if (!table) return alert('Please select a table first');
  
  const query = $('search-input').value.trim();
  const pageSizeVal = $('page-size').value;
  showAll = pageSizeVal === 'all';
  pageSize = showAll ? Number.MAX_SAFE_INTEGER : parseInt(pageSizeVal, 10);
  
  let url = `${API}/tables/${table}/data`;
  if (showAll) {
    url += `?all=true`;
  } else {
    url += `?offset=${currentPage * pageSize}&limit=${pageSize}`;
  }
  
  if (isSearch && query) {
    // Use global search endpoint
    url = `${API}/tables/${table}/search?query=${encodeURIComponent(query)}` + (showAll ? `&all=true` : `&limit=${pageSize}&offset=${currentPage * pageSize}`);
  }
  
  try {
    const res = await fetch(url);
    const data = await res.json();
    
    if (isSearch) {
      renderSearchResults(data);
    } else {
      renderTableData(data);
    }
  } catch (err) {
    $('result-meta').textContent = 'Error: ' + err.message;
  }
}

function renderTableData(data) {
  const meta = $('result-meta');
  meta.textContent = `${data.total_count?.toLocaleString() || 0} total rows`;
  
  const grid = $('grid');
  if (!data.data || data.data.length === 0) {
    grid.innerHTML = '<p class="muted">No data found</p>';
    return;
  }
  
  const table = document.createElement('table');
  
  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  data.columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  
  // Body
  const tbody = document.createElement('tbody');
  data.data.forEach(row => {
    const tr = document.createElement('tr');
    data.columns.forEach(col => {
      const td = document.createElement('td');
      const val = row[col];
      td.textContent = val == null ? '' : String(val);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  
  grid.innerHTML = '';
  grid.appendChild(table);
  
  updatePager(data.total_count);
}

function renderSearchResults(data) {
  const meta = $('result-meta');
  meta.textContent = `${data.total_matches?.toLocaleString() || 0} matches for "${data.query}"`;
  
  const grid = $('grid');
  if (!data.data || data.data.length === 0) {
    grid.innerHTML = '<p class="muted">No matches found</p>';
    return;
  }
  
  const table = document.createElement('table');
  
  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  data.columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  
  // Body
  const tbody = document.createElement('tbody');
  data.data.forEach(row => {
    const tr = document.createElement('tr');
    data.columns.forEach(col => {
      const td = document.createElement('td');
      const val = row[col];
      td.textContent = val == null ? '' : String(val);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  
  grid.innerHTML = '';
  grid.appendChild(table);
  
  updatePager(data.total_matches);
}

function updatePager(total) {
  if (showAll) {
    $('page-info').textContent = `Showing all ${total.toLocaleString()} rows`;
    $('prev-page').disabled = true;
    $('next-page').disabled = true;
    return;
  }
  const totalPages = Math.ceil(total / pageSize);
  $('page-info').textContent = `Page ${currentPage + 1} of ${totalPages}`;
  
  $('prev-page').disabled = currentPage === 0;
  $('next-page').disabled = currentPage >= totalPages - 1;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  checkBackend();
  
  $('upload-btn').onclick = uploadFile;
  $('merge-all-btn').onclick = mergeAllData;
  $('refresh-tables').onclick = refreshTables;
  $('load-data-btn').onclick = () => loadData(false);
  $('search-btn').onclick = () => {
    currentPage = 0; // Reset to first page for search
    loadData(true);
  };
  
  $('prev-page').onclick = () => {
    if (currentPage > 0) {
      currentPage--;
      loadData($('search-input').value.trim() ? true : false);
    }
  };
  
  $('next-page').onclick = () => {
    currentPage++;
    loadData($('search-input').value.trim() ? true : false);
  };
  
  // Enter key for search
  $('search-input').onkeydown = (e) => {
    if (e.key === 'Enter') {
      currentPage = 0;
      loadData(true);
    }
  };
});