#!/bin/zsh
# ============================================================
# Smart Farming Decision Support System — Startup Script
# ============================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/disease_train_env/bin/python3.10"

echo "🌾 Starting Smart Farming Decision Support System..."
echo "📁 Project: $PROJECT_DIR"

# Step 1: Start Ollama daemon if not running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🤖 Starting Ollama daemon..."
    /Applications/Ollama.app/Contents/Resources/ollama serve &> /tmp/ollama.log &
    sleep 3
    echo "✅ Ollama started"
else
    echo "✅ Ollama already running"
fi

# Step 2: Free port 8000 if occupied
if lsof -ti :8000 > /dev/null 2>&1; then
    echo "🔓 Freeing port 8000..."
    lsof -ti :8000 | xargs kill -9
    sleep 1
fi

# Step 3: Start FastAPI server using the correct Python binary
echo "🚀 Starting FastAPI server on http://127.0.0.1:8000 ..."
cd "$PROJECT_DIR"
"$PYTHON" -m uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
