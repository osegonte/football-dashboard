import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("football_dashboard.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("main")

# Add the current directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import components
from database.db_setup import init_database
from pipeline.pipeline_runner import PipelineRunner
from pipeline.scheduler import PipelineScheduler
from dashboard.app import app

def setup_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialization complete")

def run_pipeline(days_ahead=7):
    """Run the data pipeline"""
    logger.info(f"Running data pipeline for {days_ahead} days ahead...")
    
    runner = PipelineRunner()
    stats = runner.run_full_pipeline(days_ahead=days_ahead)
    
    logger.info(f"Pipeline execution complete: {stats}")
    return stats

def start_scheduler(interval_hours=12):
    """Start the pipeline scheduler"""
    logger.info(f"Starting scheduler with {interval_hours} hour interval...")
    
    scheduler = PipelineScheduler()
    scheduler.schedule_interval_run(hours=interval_hours)
    scheduler.start()

def start_dashboard():
    """Start the web dashboard"""
    logger.info("Starting web dashboard...")
    app.run(debug=False, host='0.0.0.0', port=5000)

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Football Dashboard Application")
    
    # Define command-line arguments
    parser.add_argument('--init-db', action='store_true', help="Initialize the database")
    parser.add_argument('--run-pipeline', action='store_true', help="Run the data pipeline")
    parser.add_argument('--days', type=int, default=7, help="Number of days ahead for fixture scraping")
    parser.add_argument('--start-scheduler', action='store_true', help="Start the pipeline scheduler")
    parser.add_argument('--interval', type=int, default=12, help="Scheduler interval in hours")
    parser.add_argument('--start-dashboard', action='store_true', help="Start the web dashboard")
    parser.add_argument('--all', action='store_true', help="Run all components")
    
    args = parser.parse_args()
    
    # Process arguments
    if args.init_db or args.all:
        setup_database()
    
    if args.run_pipeline or args.all:
        run_pipeline(days_ahead=args.days)
    
    if args.start_scheduler or args.all:
        if args.start_dashboard or args.all:
            # If both scheduler and dashboard are requested, run scheduler in a separate thread
            import threading
            scheduler_thread = threading.Thread(target=start_scheduler, args=(args.interval,))
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            # Start dashboard in the main thread
            start_dashboard()
        else:
            # Only scheduler, run in main thread
            start_scheduler(interval_hours=args.interval)
    elif args.start_dashboard or args.all:
        # Only dashboard, run in main thread
        start_dashboard()
    
    # If no arguments provided, show help
    if not (args.init_db or args.run_pipeline or args.start_scheduler or args.start_dashboard or args.all):
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)