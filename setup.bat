@echo off
REM Smart Meeting AI - Windows Development Setup Script

echo 🚀 Setting up Smart Meeting AI Development Environment...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.9+ is required but not installed
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js 18+ is required but not installed
    pause
    exit /b 1
)

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Docker is not installed - you won't be able to use the containerized setup
)

echo ✅ Prerequisites check passed

REM Setup Backend
echo 📦 Setting up Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

REM Download spaCy model
python -m spacy download en_core_web_sm

echo ✅ Backend setup complete

REM Setup Frontend
echo 📦 Setting up Frontend...
cd ..\frontend
call npm install

echo ✅ Frontend setup complete

REM Create .env file from template
cd ..
if not exist .env (
    copy .env.example .env
    echo 📝 Created .env file from template
    echo ⚠️  Please update the .env file with your actual API keys and configuration
)

echo.
echo 🎉 Setup complete!
echo.
echo Quick Start Commands:
echo ====================
echo.
echo 🐳 Using Docker (Recommended):
echo   docker-compose up --build
echo.
echo 🔧 Manual Setup:
echo   1. Backend: cd backend && uvicorn app.main:app --reload
echo   2. Frontend: cd frontend && npm start
echo   3. Database: Start MongoDB on localhost:27017
echo.
echo 📖 Documentation:
echo   - API Docs: http://localhost:8000/docs
echo   - Frontend: http://localhost:3000
echo.
echo ⚙️  Next Steps:
echo   1. Update .env with your API keys
echo   2. Start MongoDB (if not using Docker)
echo   3. Run the application
echo.
echo Happy coding! 🎯
pause