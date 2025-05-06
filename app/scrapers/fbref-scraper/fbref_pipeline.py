#!/usr/bin/env python3
"""
FBref Team Data Pipeline

This script orchestrates the entire process:
1. Extract teams from existing data
2. Prepare team names for FBref
3. Scrape team data from FBref
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fbref_pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("fbref_pipeline")

# Make sure the modules are importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fbref_team_preparation import FBrefTeamPreparation
from fbref_team_scraper import FBrefTeamScraper

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='FBref Team Data Pipeline')
    parser.add_argument('--prepare', action='store_true',
                       help='Prepare teams for FBref scraping')
    parser.add_argument('--scrape', action='store_true',
                       help='Scrape team data from FBref')
    parser.add_argument('--all', action='store_true',
                       help='Run the complete pipeline')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit the number of teams (0 for no limit)')
    parser.add_argument('--verified-only', action='store_true',
                       help='Only scrape verified teams')
    parser.add_argument('--output-dir', type=str, default='fbref_data',
                       help='Output directory for data files')
    
    args = parser.parse_args()
    
    # Default to running everything if no specific step is requested
    run_all = args.all or not (args.prepare or args.scrape)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Step 1: Prepare teams
    if run_all or args.prepare:
        logger.info("=== Starting team preparation ===")
        
        prep = FBrefTeamPreparation(data_dir=args.output_dir)
        
        # Get teams from both files and database
        file_teams = prep.extract_teams_from_matches()
        db_teams = prep.get_teams_from_database()
        
        # Combine teams
        teams_set = set(file_teams)
        teams_set.update([team['name'] for team in db_teams])
        teams_list = list(teams_set)
        
        # Apply limit if specified
        if args.limit > 0:
            teams_list = teams_list[:args.limit]
        
        logger.info(f"Preparing {len(teams_list)} teams for FBref")
        
       # Prepare teams for FBref
        prepared_teams = prep.prepare_teams_for_fbref(teams_list)
        
        # Save prepared teams
        output_file = prep.save_prepared_teams(prepared_teams)
        
        verified_count = sum(1 for t in prepared_teams if t.get('verified', False))
        logger.info(f"Team preparation complete. Verified: {verified_count}, Total: {len(prepared_teams)}")
    
    # Step 2: Scrape team data
    if run_all or args.scrape:
        logger.info("=== Starting team data scraping ===")
        
        scraper = FBrefTeamScraper(data_dir=args.output_dir)
        
        # Load prepared teams
        teams = scraper.load_prepared_teams()
        
        # Filter verified teams if requested
        if args.verified_only:
            original_count = len(teams)
            teams = [t for t in teams if t.get('verified', False)]
            logger.info(f"Filtered from {original_count} to {len(teams)} verified teams")
        
        # Apply limit if specified
        if args.limit > 0:
            teams = teams[:args.limit]
        
        logger.info(f"Scraping {len(teams)} teams from FBref")
        
        # Scrape teams
        stats = scraper.scrape_multiple_teams(teams)
        
        logger.info(f"Team scraping complete. Success: {stats['success']}, Failed: {stats['failed']}")
    
    logger.info("=== FBref Pipeline Complete ===")
    
    # Print summary
    if run_all:
        print("\n=== FBref Pipeline Summary ===")
        print(f"Output Directory: {args.output_dir}")
        if 'prepared_teams' in locals():
            print(f"Teams Prepared: {len(prepared_teams)}")
            print(f"Verified Teams: {verified_count}")
        if 'stats' in locals():
            print(f"Teams Scraped: {stats['total']}")
            print(f"Successful Scrapes: {stats['success']}")
            print(f"Failed Scrapes: {stats['failed']}")

if __name__ == "__main__":
    try:
        start_time = datetime.now()
        main()
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Pipeline completed in {execution_time:.2f} seconds")
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)