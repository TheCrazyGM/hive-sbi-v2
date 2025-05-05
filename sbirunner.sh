#!/bin/bash

# Hive SBI Runner Script
# This script uses the modular approach with the hive_sbi package

# Set the Python interpreter
PYTHON_BIN=".venv/bin/python3"

# Set the base directory
BASE_DIR="."

# Function to run a specific module
run_module() {
  module_name=$1
  echo "Running $module_name..."
  cd $BASE_DIR && $PYTHON_BIN -m hive_sbi.hsbi.runner "$module_name"
  echo "Finished $module_name"
  echo ""
}

# Check if a specific module was requested
if [ "$1" != "" ]; then
  run_module "$1"
  exit 0
fi

# Run all modules in sequence
echo "Starting Hive SBI processing cycle at $(date)"
echo "----------------------------------------"

# Run all modules using the centralized runner
cd $BASE_DIR && $PYTHON_BIN -m hive_sbi.hsbi.runner

echo "----------------------------------------"
echo "Completed Hive SBI processing cycle at $(date)"

