import os

# Database settings
DATABASE_PATH = os.environ.get('FOOTBALL_DB_PATH', 'database/football_data.db')

# Scraper settings
DATA_DIR = os.environ.get('FOOTBALL_DATA_DIR', 'sofascore_data')
SCRAPE_DAYS_AHEAD = int(os.environ.get('FOOTBALL_SCRAPE_DAYS', '7'))

# Dashboard settings
DEBUG_MODE = os.environ.get('FOOTBALL_DEBUG', 'False').lower() == 'true'
HOST = os.environ.get('FOOTBALL_HOST', '0.0.0.0')
PORT = int(os.environ.get('FOOTBALL_PORT', '5000'))

# Scheduler settings
SCHEDULER_INTERVAL_HOURS = int(os.environ.get('FOOTBALL_SCHEDULER_INTERVAL', '12'))
DAILY_RUN_TIME = os.environ.get('FOOTBALL_DAILY_RUN_TIME', "00:00")  # Midnight