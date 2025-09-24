#!/bin/bash

# Smart Meeting AI - Development Setup Script

echo "🚀 Setting up Smart Meeting AI Development Environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.9+ is required but not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 18+ is required but not installed"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed - you won't be able to use the containerized setup"
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo "📦 Setting up Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

echo "✅ Backend setup complete"

# Setup Frontend
echo "📦 Setting up Frontend..."
cd ../frontend
npm install

echo "✅ Frontend setup complete"

# Create .env file from template
cd ..
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file from template"
    echo "⚠️  Please update the .env file with your actual API keys and configuration"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Quick Start Commands:"
echo "===================="
echo ""
echo "🐳 Using Docker (Recommended):"
echo "  docker-compose up --build"
echo ""
echo "🔧 Manual Setup:"
echo "  1. Backend: cd backend && uvicorn app.main:app --reload"
echo "  2. Frontend: cd frontend && npm start"
echo "  3. Database: Start MongoDB on localhost:27017"
echo ""
echo "📖 Documentation:"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "⚙️  Next Steps:"
echo "  1. Update .env with your API keys"
echo "  2. Start MongoDB (if not using Docker)"
echo "  3. Run the application"
echo ""
echo "Happy coding! 🎯"