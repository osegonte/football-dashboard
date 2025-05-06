import os
import json
import time
import random
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fbref_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("fbref_scraper")

class FBrefTeamScraper:
    """
    Scraper for collecting team data from FBref
    """
    
    def __init__(self, data_dir="fbref_data"):
        """Initialize with data directory"""
        self.data_dir = data_dir
        
        # Create data directories if they don't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self.teams_dir = os.path.join(data_dir, "teams")
        if not os.path.exists(self.teams_dir):
            os.makedirs(self.teams_dir)
        
        # User agents for making requests
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
    
    def get_random_headers(self):
        """Get random user agent headers"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
    
    def load_prepared_teams(self, filename="fbref_teams.json"):
        """
        Load prepared teams from JSON file
        
        Args:
            filename: Input filename
            
        Returns:
            List of team dictionaries
        """
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Prepared teams file not found: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract all teams
        if 'all_teams' in data:
            teams = data['all_teams']
        else:
            teams = []
            # Try to extract from teams_by_league
            if 'teams_by_league' in data:
                for league, league_teams in data['teams_by_league'].items():
                    teams.extend(league_teams)
        
        logger.info(f"Loaded {len(teams)} teams from {file_path}")
        return teams
    
    def scrape_team_data(self, team):
        """
        Scrape data for a single team from FBref
        
        Args:
            team: Team dictionary with name and fbref_url
            
        Returns:
            Dictionary with scraped team data
        """
        team_name = team['name']
        team_url = team.get('fbref_url')
        
        # If no URL, try to construct one
        if not team_url:
            formatted_name = team.get('formatted_name')
            if not formatted_name:
                formatted_name = team['name'].lower().replace(' ', '-')
            
            team_url = f"https://fbref.com/en/squads/{formatted_name}/Stats"
        
        logger.info(f"Scraping data for {team_name} from {team_url}")
        
        try:
            # Make request to FBref
            headers = self.get_random_headers()
            response = requests.get(team_url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get {team_name} data: HTTP {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract team data
            team_data = {
                'name': team_name,
                'fbref_url': team_url,
                'scraped_at': datetime.now().isoformat(),
                'stats': {}
            }
            
            # Extract team info
            info_div = soup.select_one('div#meta')
            if info_div:
                # Extract stadium
                stadium_p = info_div.select_one('p:contains("Stadium:")')
                if stadium_p:
                    stadium_text = stadium_p.text.replace('Stadium:', '').strip()
                    team_data['stadium'] = stadium_text
                
                # Extract manager
                manager_p = info_div.select_one('p:contains("Manager:")')
                if manager_p:
                    manager_text = manager_p.text.replace('Manager:', '').strip()
                    team_data['manager'] = manager_text
            
            # Extract team stats tables
            stats_tables = soup.select('table.stats_table')
            
            for table in stats_tables:
                # Get table ID or caption
                table_id = table.get('id', '')
                caption = table.select_one('caption')
                table_name = caption.text.strip() if caption else table_id
                
                if not table_name:
                    continue
                
                # Try to convert table to DataFrame
                try:
                    df = pd.read_html(str(table))[0]
                    
                    # Convert DataFrame to dictionary
                    table_data = df.to_dict(orient='records')
                    
                    # Add to team stats
                    team_data['stats'][table_name] = table_data
                    
                    logger.info(f"Extracted {table_name} stats for {team_name}")
                except Exception as e:
                    logger.warning(f"Error extracting {table_name} stats: {str(e)}")
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error scraping {team_name}: {str(e)}")
            return None
    
    def save_team_data(self, team_name, team_data):
        """
        Save team data to JSON file
        
        Args:
            team_name: Team name
            team_data: Team data dictionary
            
        Returns:
            Path to saved file
        """
        # Create safe filename
        safe_name = team_name.lower().replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}_fbref_data.json"
        file_path = os.path.join(self.teams_dir, filename)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, indent=2)
        
        logger.info(f"Saved {team_name} data to {file_path}")
        return file_path
    
    def scrape_multiple_teams(self, teams, delay_min=3, delay_max=7):
        """
        Scrape data for multiple teams
        
        Args:
            teams: List of team dictionaries
            delay_min: Minimum delay between requests in seconds
            delay_max: Maximum delay between requests in seconds
            
        Returns:
            Dictionary with scraping statistics
        """
        logger.info(f"Starting to scrape {len(teams)} teams")
        
        stats = {
            "total": len(teams),
            "success": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        for i, team in enumerate(teams):
            team_name = team['name']
            
            logger.info(f"Processing team {i+1}/{len(teams)}: {team_name}")
            
            try:
                # Scrape team data
                team_data = self.scrape_team_data(team)
                
                if team_data:
                    # Save team data
                    self.save_team_data(team_name, team_data)
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                # Add delay between requests
                if i < len(teams) - 1:
                    delay = random.uniform(delay_min, delay_max)
                    logger.info(f"Waiting {delay:.2f} seconds before next team")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error processing {team_name}: {str(e)}")
                stats["failed"] += 1
        
        stats["end_time"] = datetime.now().isoformat()
        
        # Save stats
        stats_file = os.path.join(self.data_dir, "fbref_scrape_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Team scraping completed: {stats['success']} success, {stats['failed']} failed")
        return stats

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FBref Team Data Scraper')
    parser.add_argument('--file', type=str, default='fbref_teams.json',
                       help='Input file with prepared teams')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit the number of teams to scrape (0 for no limit)')
    parser.add_argument('--verified-only', action='store_true',
                       help='Only scrape verified teams')
    parser.add_argument('--team-name', type=str,
                       help='Scrape a specific team by name')
    
    args = parser.parse_args()
    
    scraper = FBrefTeamScraper()
    
    if args.team_name:
        # Scrape a single team
        team = {'name': args.team_name}
        print(f"Scraping team: {args.team_name}")
        team_data = scraper.scrape_team_data(team)
        
        if team_data:
            file_path = scraper.save_team_data(args.team_name, team_data)
            print(f"Team data saved to: {file_path}")
        else:
            print(f"Failed to scrape {args.team_name}")
    else:
        # Load teams
        teams = scraper.load_prepared_teams(args.file)
        
        # Filter verified teams if requested
        if args.verified_only:
            teams = [t for t in teams if t.get('verified', False)]
            print(f"Filtered to {len(teams)} verified teams")
        
        # Apply limit if specified
        if args.limit > 0:
            teams = teams[:args.limit]
        
        print(f"Scraping {len(teams)} teams...")
        
        # Scrape teams
        stats = scraper.scrape_multiple_teams(teams)
        
        print("\n=== FBref Team Scraping Summary ===")
        print(f"Total Teams: {stats['total']}")
        print(f"Successful: {stats['success']}")
        print(f"Failed: {stats['failed']}")

if __name__ == "__main__":
    main()