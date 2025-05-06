import time
import schedule
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.pipeline_runner import PipelineRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("scheduler")

class PipelineScheduler:
    """
    Scheduler for running the football data pipeline at regular intervals
    """
    
    def __init__(self):
        """Initialize the pipeline scheduler"""
        self.runner = PipelineRunner()
        self.running = False
    
    def run_pipeline_job(self):
        """Run the pipeline as a scheduled job"""
        try:
            logger.info("Running scheduled pipeline job...")
            start_time = time.time()
            
            # Run the full pipeline
            stats = self.runner.run_full_pipeline()
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            logger.info(f"Pipeline job completed in {execution_time:.2f} seconds")
            logger.info(f"Statistics: {stats}")
            
            # Write job execution record
            self._record_job_execution(True, stats, execution_time)
            
        except Exception as e:
            logger.error(f"Error in pipeline job: {str(e)}")
            self._record_job_execution(False, {"error": str(e)}, 0)
    
    def _record_job_execution(self, success, stats, execution_time):
        """
        Record job execution details to a log file
        
        Args:
            success: Whether the job was successful
            stats: Job statistics
            execution_time: Execution time in seconds
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create log entry
            entry = {
                "timestamp": timestamp,
                "success": success,
                "execution_time": f"{execution_time:.2f}s",
                "stats": stats
            }
            
            # Append to log file
            with open("job_executions.log", "a") as f:
                f.write(f"{entry}\n")
                
        except Exception as e:
            logger.error(f"Error recording job execution: {str(e)}")
    
    def schedule_daily_run(self, time_str="00:00"):
        """
        Schedule the pipeline to run daily at a specific time
        
        Args:
            time_str: Time to run in HH:MM format (24-hour)
        """
        logger.info(f"Scheduling daily pipeline run at {time_str}")
        schedule.every().day.at(time_str).do(self.run_pipeline_job)
    
    def schedule_interval_run(self, hours=12):
        """
        Schedule the pipeline to run at regular intervals
        
        Args:
            hours: Interval in hours
        """
        logger.info(f"Scheduling pipeline run every {hours} hours")
        schedule.every(hours).hours.do(self.run_pipeline_job)
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting scheduler...")
        
        # Run once immediately at startup
        self.run_pipeline_job()
        
        # Then run according to schedule
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scheduler...")
        self.running = False


def run_scheduler():
    """Run the scheduler as a standalone script"""
    scheduler = PipelineScheduler()
    
    # Schedule pipeline runs
    scheduler.schedule_daily_run("00:00")  # Run at midnight
    scheduler.schedule_interval_run(12)    # Also run every 12 hours
    
    try:
        # Start the scheduler
        scheduler.start()
    except KeyboardInterrupt:
        # Stop on Ctrl+C
        scheduler.stop()
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    run_scheduler()