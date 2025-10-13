#!/bin/bash
# Quick start script for Claude Agent Chat Web Interface

set -e

# Function to run pip with best available command
run_pip() {
    if command -v python3 &> /dev/null; then
        python3 -m pip "$@"
    elif command -v pip3 &> /dev/null; then
        pip3 "$@"
    elif command -v pip &> /dev/null; then
        pip "$@"
    else
        echo "❌ Error: No pip command found (tried: python3 -m pip, pip3, pip)"
        echo "   Please install Python and pip first"
        return 1
    fi
}

echo "🚀 Starting Claude Agent Chat Web Interface..."
echo ""

# Check if we're in the right directory
if [ ! -f "web/backend/api.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Smart API key check - tries multiple sources
echo "🔑 Checking API key configuration..."

# Try to load .env if it exists
if [ -f ".env" ]; then
    set -a  # Export all variables
    source .env 2>/dev/null
    set +a
fi

# Check if Python backend can access the key from ANY source
KEY_CHECK=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from settings_manager import get_settings
    s = get_settings()
    key = s.get_anthropic_api_key()
    if key:
        print('OK')
    else:
        print('MISSING')
except Exception as e:
    print('ERROR')
" 2>/dev/null)

if [ "$KEY_CHECK" = "OK" ]; then
    echo "✅ API key configured and accessible"
elif [ "$KEY_CHECK" = "MISSING" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not found in:"
    echo "   • Shell environment (\$ANTHROPIC_API_KEY)"
    echo "   • .env file"
    echo "   • settings.json"
    echo ""
    echo "   Configure with one of these methods:"
    echo "   1. export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "   2. Create .env file: echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env"
    echo "   3. Run settings menu: python3 coordinator_with_memory.py"
    echo ""
    read -p "   Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "⚠️  Could not verify API key (settings_manager not available)"
    echo "   Continuing anyway..."
fi
echo ""

# Start databases
echo "📊 Starting databases..."
docker-compose up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to initialize..."
sleep 3

# Start backend
echo "🔧 Starting FastAPI backend..."

# Install dependencies (show output on first run)
if [ ! -f "web/backend/.installed" ]; then
    echo "📦 Installing backend dependencies (first run)..."
    if ! run_pip install -r web/backend/requirements-web.txt; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    touch web/backend/.installed
    echo "✅ Dependencies installed"
else
    run_pip install -r web/backend/requirements-web.txt > /dev/null 2>&1
fi

# Run backend from project root so relative paths work
python3 web/backend/api.py &
BACKEND_PID=$!

# Wait for backend to be ready with health check
echo "⏳ Waiting for backend to be ready..."
BACKEND_READY=false
for i in {1..15}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        BACKEND_READY=true
        break
    fi
    sleep 1
    if [ $((i % 5)) -eq 0 ]; then
        echo "   Still waiting... ($i/15)"
    fi
done

if [ "$BACKEND_READY" = false ]; then
    echo "⚠️  Backend is taking longer than expected"
    echo "   Check logs or visit http://localhost:8000/api/health manually"
fi

# Start frontend
echo "🎨 Starting Next.js frontend..."
cd web/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo "✅ All services started!"
echo ""
echo "📚 Access points:"
echo "   🌐 Web UI:       http://localhost:3000"
echo "   🔌 Backend API:  http://localhost:8000"
echo "   📖 API Docs:     http://localhost:8000/docs"
echo ""
echo "🛑 To stop all services:"
echo "   Press Ctrl+C, then run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   docker-compose down"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose down; echo '✅ Stopped'; exit 0" INT

echo "Press Ctrl+C to stop all services..."
wait
