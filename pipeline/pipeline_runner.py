import os
import sys
import time
import logging
from datetime import date, timedelta
import pandas as pd

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.daily_match_scraper import AdvancedSofaScoreScraper
from scrapers.team_data_processor import TeamDataProcessor
from database.db_setup import init_database, get_db_session
from database.operations import DBOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("pipeline")

class PipelineRunner:
    """
    Coordinates the execution of the data pipeline for football match and team data
    """
    
    def __init__(self, data_dir="sofascore_data"):
        """
        Initialize the pipeline runner
        
        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def run_full_pipeline(self, days_ahead=7):
        """
        Run the complete pipeline: scrape matches, process teams, prepare for team data scraping
        
        Args:
            days_ahead: Number of days to look ahead for fixtures
            
        Returns:
            Dictionary with pipeline statistics
        """
        logger.info("Starting full pipeline run...")
        
        # Initialize the database if needed
        init_database()
        
        # Step 1: Scrape match data
        match_stats = self.scrape_matches(days_ahead)
        
        # Step 2: Process match data to extract teams
        team_stats = self.process_match_data()
        
        # Step 3: Prepare team list for team data scraping
        teams_to_scrape = self.prepare_team_list()
        
        # Combine statistics
        stats = {
            "matches_scraped": match_stats.get("total_matches", 0),
            "files_created": match_stats.get("days_processed", 0),
            "matches_processed": team_stats.get("matches", 0),
            "teams_extracted": team_stats.get("teams", 0),
            "leagues_extracted": team_stats.get("leagues", 0),
            "teams_to_scrape": teams_to_scrape
        }
        
        logger.info(f"Pipeline completed successfully: {stats}")
        return stats
    
    def scrape_matches(self, days_ahead=7):
        """
        Scrape match data for upcoming days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            Dictionary with scraping statistics
        """
        logger.info(f"Scraping match data for next {days_ahead} days...")
        
        try:
            # Initialize scraper
            scraper = AdvancedSofaScoreScraper()
            
            # Calculate date range
            today = date.today()
            end_date = today + timedelta(days=days_ahead)
            
            # Fetch matches
            all_matches, total_matches = scraper.fetch_matches_for_date_range(today, end_date)
            
            stats = {
                "days_processed": len(all_matches),
                "total_matches": total_matches
            }
            
            logger.info(f"Match scraping completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error scraping matches: {str(e)}")
            return {"days_processed": 0, "total_matches": 0}
    
    def process_match_data(self):
        """
        Process match data to extract and store team information
        
        Returns:
            Dictionary with processing statistics
        """
        logger.info("Processing match data to extract team information...")
        
        try:
            # Initialize team data processor
            processor = TeamDataProcessor(self.data_dir)
            
            # Process all match files
            stats = processor.process_all_match_files()
            
            logger.info(f"Team data processing completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing match data: {str(e)}")
            return {"files": 0, "matches": 0, "teams": 0, "leagues": 0}
    
    def prepare_team_list(self):
        """
        Prepare list of teams for team data scraping
        
        Returns:
            Number of teams prepared for scraping
        """
        logger.info("Preparing team list for team data scraping...")
        
        try:
            # Initialize team data processor
            processor = TeamDataProcessor(self.data_dir)
            
            # Generate team list
            num_teams = processor.get_team_list_for_scraper()
            
            logger.info(f"Prepared {num_teams} teams for scraping")
            return num_teams
            
        except Exception as e:
            logger.error(f"Error preparing team list: {str(e)}")
            return 0
    
    def analyze_stored_data(self):
        """
        Analyze the data stored in the database
        
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing stored data...")
        
        try:
            session = get_db_session()
            
            # Get counts
            match_count = session.query(DBOperations.get_all_matches()).count()
            team_count = session.query(DBOperations.get_all_teams()).count()
            league_count = session.query(DBOperations.get_all_leagues()).count()
            
            # Get upcoming matches
            upcoming_matches = DBOperations.get_upcoming_matches()
            
            analysis = {
                "match_count": match_count,
                "team_count": team_count,
                "league_count": league_count,
                "upcoming_match_count": len(upcoming_matches)
            }
            
            logger.info(f"Data analysis completed: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            return {
                "match_count": 0,
                "team_count": 0, 
                "league_count": 0,
                "upcoming_match_count": 0
            }
        finally:
            if 'session' in locals():
                session.close()


def run_pipeline():
    """Run the full pipeline as a standalone script"""
    runner = PipelineRunner()
    stats = runner.run_full_pipeline()
    
    print("\n=== Pipeline Execution Summary ===")
    print(f"Matches Scraped: {stats['matches_scraped']}")
    print(f"Files Created: {stats['files_created']}")
    print(f"Matches Processed: {stats['matches_processed']}")
    print(f"Teams Extracted: {stats['teams_extracted']}")
    print(f"Leagues Extracted: {stats['leagues_extracted']}")
    print(f"Teams Ready for Scraping: {stats['teams_to_scrape']}")


if __name__ == "__main__":
    run_pipeline()