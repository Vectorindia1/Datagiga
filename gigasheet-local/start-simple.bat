@echo off
echo 🚀 Starting Local Gigasheet Clone...
echo.

echo ✅ Python: 
python --version
echo ✅ Node.js:
node --version
echo.

echo 📊 Starting Backend (FastAPI + DuckDB)...
echo    Backend URL: http://localhost:8000
cd backend
start "Gigasheet Backend" python main.py
cd ..

echo ⏳ Waiting for backend...
timeout /t 8 /nobreak > nul

echo 🎨 Starting Frontend (React + AG Grid)...
echo    Frontend URL: http://localhost:3000
cd frontend
start "Gigasheet Frontend" npm start
cd ..

echo.
echo 🎉 Both services are starting!
echo.
echo 📱 Access your application:
echo    🌐 Frontend: http://localhost:3000
echo    🔧 Backend API: http://localhost:8000
echo.
echo 📋 To process your Excel files:
echo    1. Open http://localhost:3000
echo    2. Click 'Smart Incremental Merge'
echo    3. Wait for processing
echo    4. Explore your data!
echo.

pause
start http://localhost:3000