import sys
import os

# Add both potential module paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

# Try to import from database
try:
    from database.db_setup import init_database
    from pipeline.pipeline_runner import PipelineRunner
    from dashboard.app import app
    print("Using root-level modules")
except ImportError:
    # If that fails, try the app directory
    from app.database.db_setup import init_database
    from app.pipeline.pipeline_runner import PipelineRunner
    from app.dashboard.app import app
    print("Using app-level modules")

import argparse

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Football Dashboard Application")
    
    # Define command-line arguments
    parser.add_argument("--init-db", action="store_true", help="Initialize the database")
    parser.add_argument("--run-pipeline", action="store_true", help="Run the data pipeline")
    parser.add_argument("--days", type=int, default=7, help="Number of days ahead for fixture scraping")
    parser.add_argument("--start-scheduler", action="store_true", help="Start the pipeline scheduler")
    parser.add_argument("--interval", type=int, default=12, help="Scheduler interval in hours")
    parser.add_argument("--start-dashboard", action="store_true", help="Start the web dashboard")
    parser.add_argument("--all", action="store_true", help="Run all components")
    parser.add_argument("--port", type=int, default=8080, help="Port for the dashboard (default: 8080)")
    
    args = parser.parse_args()
    
    # Process arguments
    if args.init_db or args.all:
        print("Initializing database...")
        init_database()
    
    if args.run_pipeline or args.all:
        print(f"Running pipeline for {args.days} days ahead...")
        runner = PipelineRunner()
        runner.run_full_pipeline(days_ahead=args.days)
    
    if args.start_dashboard or args.all:
        print(f"Starting dashboard on port {args.port}...")
        app.run(debug=True, host="0.0.0.0", port=args.port)
    
    # If no arguments provided, show help
    if not (args.init_db or args.run_pipeline or args.start_scheduler or args.start_dashboard or args.all):
        parser.print_help()

if __name__ == "__main__":
    main()

