#!/bin/bash

# Quickstart script for Multi-Agent Conversation System with Memory
# This script sets up and starts everything you need

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Multi-Agent Conversation System - Quick Start Setup    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "   Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "   Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  ANTHROPIC_API_KEY not set${NC}"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
    echo ""
    echo "Get your key from: https://console.anthropic.com/"
    echo ""
    read -p "Press Enter once you've set your API key, or Ctrl+C to exit..."

    # Check again
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}❌ API key still not set. Exiting.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ ANTHROPIC_API_KEY is set${NC}"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "🚀 Starting setup..."
echo "────────────────────────────────────────────────────────────"
echo ""

# Step 1: Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 2: Start Docker services
echo ""
echo "🐳 Starting database services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
for i in {1..30}; do
    if docker exec agent-chat-postgres pg_isready -U agent_user -d agent_conversations > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ PostgreSQL failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Check Qdrant
for i in {1..30}; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Qdrant is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Qdrant failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Step 3: Test database connection
echo ""
echo "🔍 Testing database connection..."
python3 -c "
from db_manager import DatabaseManager
try:
    db = DatabaseManager()
    print('${GREEN}✅ Database connection successful${NC}')
    db.close()
except Exception as e:
    print('${RED}❌ Database connection failed:', str(e), '${NC}')
    exit(1)
"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                   🎉 Setup Complete! 🎉                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Services running:"
echo "   • PostgreSQL:  localhost:5432"
echo "   • Qdrant:      localhost:6333"
echo "   • Qdrant UI:   http://localhost:6333/dashboard"
echo ""
echo "🎮 To start using the system:"
echo "   python3 coordinator_with_memory.py"
echo ""
echo "📚 Useful commands:"
echo "   docker-compose ps       # Check service status"
echo "   docker-compose logs     # View logs"
echo "   docker-compose down     # Stop services"
echo "   docker-compose restart  # Restart services"
echo ""
echo "📖 See SETUP_DATABASE.md for more details"
echo ""
