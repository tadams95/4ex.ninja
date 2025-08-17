#!/bin/bash

# Step 1.2 Launcher Script
# Comprehensive Currency Pair Backtesting Plan

echo "🚀 Starting Step 1.2: Data Acquisition & Preparation"
echo "=============================================="

# Navigate to backend directory
cd "$(dirname "$0")/4ex.ninja-backend" || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if required directories exist
echo "🔍 Checking directory structure..."
mkdir -p logs
mkdir -p backtest_results
mkdir -p data

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "📋 Installing requirements..."
    pip install -q -r requirements.txt
fi

# Check for environment variables
echo "🔧 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure OANDA credentials are configured."
fi

# Execute Step 1.2
echo "🏃‍♂️ Executing Step 1.2 pipeline..."
echo "=============================================="

python scripts/execute_step_1_2.py

execution_status=$?

echo "=============================================="
if [ $execution_status -eq 0 ]; then
    echo "✅ Step 1.2 completed successfully!"
    echo "📊 Check backtest_results/step_1_2_execution/ for detailed reports"
    echo "🚀 Ready to proceed to Step 2.1: Strategy Parameter Configuration"
else
    echo "❌ Step 1.2 failed with exit code $execution_status"
    echo "📋 Check logs/step_1_2_execution.log for details"
fi

echo "=============================================="
exit $execution_status
