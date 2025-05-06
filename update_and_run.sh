#!/bin/bash

# Update script for Football Dashboard project
# This script applies fixes to the session binding error and runs the updated pipeline

echo "===== Football Dashboard Update Script ====="
echo "Checking environment..."

# Check if we're in a virtual environment
if [[ -z $VIRTUAL_ENV ]]; then
  echo "Activating virtual environment..."
  
  # Try to activate the virtual environment
  if [[ -f "venv_py311/bin/activate" ]]; then
    source venv_py311/bin/activate
  elif [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
  else
    echo "Error: Unable to find virtual environment. Please activate manually."
    exit 1
  fi
else
  echo "Already in virtual environment: $VIRTUAL_ENV"
fi

# Check dependencies
echo "Checking dependencies..."
pip install -r requirements.txt

# Create backup of existing files
echo "Creating backups..."
mkdir -p backups

# Backup existing files
if [[ -f "scrapers/team_data_processor.py" ]]; then
  cp scrapers/team_data_processor.py backups/team_data_processor.py.bak
fi

if [[ -f "pipeline/pipeline_runner.py" ]]; then
  cp pipeline/pipeline_runner.py backups/pipeline_runner.py.bak
fi

# Create the fixed files
echo "Installing fixed files..."

# Create team_data_processor_fixed.py
cp scrapers/team_data_processor_fixed.py scrapers/

# Install the new team data scraper
echo "Installing team data scraper..."
cp scrapers/team_data_scraper.py scrapers/

# Update pipeline runner
echo "Updating pipeline runner..."
cp pipeline/pipeline_runner_updated.py pipeline/pipeline_runner.py

# Create directory for team data
mkdir -p sofascore_data/teams

# Run the updated pipeline
echo "Initializing database..."
python main.py --init-db

echo "Running pipeline with team data scraping..."
python pipeline/pipeline_runner.py --days 7 --team-limit 20

echo "Starting dashboard..."
python main.py --start-dashboard

echo "Done!"