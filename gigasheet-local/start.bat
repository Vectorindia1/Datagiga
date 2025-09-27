@echo off
echo 🚀 Starting Local Gigasheet Clone...

echo.
echo 📦 Starting backend service...
cd backend
start "Backend" cmd /k "py main.py"
cd ..

echo.
echo 🎨 Starting frontend service...
cd frontend
start "Frontend" cmd /k "npm start"
cd ..

echo.
echo ✅ Services starting in separate windows!
echo 📊 Backend API: http://localhost:8000
echo 🎨 Frontend: http://localhost:3000
echo 📁 Data folder: %CD%\data (place your Excel files here)
echo.
echo Features available:
echo ✅ Upload and process massive CSV files
echo ✅ Merge multiple Excel files  
echo ✅ Real-time filtering and search
echo ✅ Handle 1 crore+ rows efficiently
echo.
echo Close the terminal windows to stop services
pause