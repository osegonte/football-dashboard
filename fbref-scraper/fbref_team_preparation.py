import os
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import logging
from database.operations import DBOperations

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

class FBrefTeamPreparation:
    """
    Prepares team data for FBref scraping by:
    1. Extracting teams from existing match data
    2. Formatting team names for FBref URLs
    3. Generating a clean list of teams to scrape
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
    
    def extract_teams_from_matches(self, match_files_dir="sofascore_data/daily"):
        """
        Extract team names from existing match data files
        
        Args:
            match_files_dir: Directory containing match CSV files
            
        Returns:
            Set of unique team names
        """
        logger.info(f"Extracting teams from match files in {match_files_dir}")
        
        teams = set()
        
        if not os.path.exists(match_files_dir):
            logger.warning(f"Match directory {match_files_dir} not found")
            return teams
        
        # Process each match file
        for filename in os.listdir(match_files_dir):
            if filename.endswith('.csv') and filename.startswith('matches_'):
                file_path = os.path.join(match_files_dir, filename)
                
                try:
                    # Read the match data
                    matches_df = pd.read_csv(file_path)
                    
                    # Extract home and away teams
                    if 'home_team' in matches_df.columns:
                        teams.update(matches_df['home_team'].dropna().unique())
                    
                    if 'away_team' in matches_df.columns:
                        teams.update(matches_df['away_team'].dropna().unique())
                    
                    logger.info(f"Processed {filename}, total teams so far: {len(teams)}")
                
                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
        
        return teams
    
    def get_teams_from_database(self):
        """
        Get teams from the database
        
        Returns:
            List of team dictionaries with id, name, country, and league
        """
        logger.info("Getting teams from database")
        
        try:
            # Get all teams from database
            teams_db = DBOperations.get_all_teams()
            
            teams = []
            for team in teams_db:
                teams.append({
                    'id': team.id,
                    'name': team.name,
                    'country': team.country if team.country else None,
                    'league': team.league.name if team.league else None
                })
            
            logger.info(f"Got {len(teams)} teams from database")
            return teams
            
        except Exception as e:
            logger.error(f"Error getting teams from database: {str(e)}")
            return []
    
    def format_team_name_for_fbref(self, team_name):
        """
        Format team name for FBref URL
        
        Args:
            team_name: Original team name
            
        Returns:
            Formatted team name for FBref URL
        """
        # Remove special characters and replace spaces with hyphens
        formatted = team_name.lower()
        formatted = ''.join(c for c in formatted if c.isalnum() or c.isspace())
        formatted = formatted.strip().replace(' ', '-')
        
        # Handle specific team name mappings that might be different on FBref
        mappings = {
            'manchester-united': 'man-united',
            'manchester-city': 'man-city',
            'tottenham-hotspur': 'tottenham',
            'wolverhampton-wanderers': 'wolves',
            'west-ham-united': 'west-ham',
            # Add more mappings as needed
        }
        
        return mappings.get(formatted, formatted)
    
    def check_team_on_fbref(self, team_name, formatted_name=None):
        """
        Check if a team exists on FBref and get the correct URL
        
        Args:
            team_name: Original team name
            formatted_name: Pre-formatted name (optional)
            
        Returns:
            Dictionary with team info including FBref URL if found
        """
        if formatted_name is None:
            formatted_name = self.format_team_name_for_fbref(team_name)
        
        # Try direct URL first
        base_url = "https://fbref.com/en/squads/"
        
        # List of URL patterns to try
        url_patterns = [
            f"{formatted_name}",  # Simple formatted name
            f"{formatted_name}-Stats",  # With Stats suffix
            f"{formatted_name}-Football-Club-Stats",  # FC suffix
            f"{formatted_name}-FC-Stats",  # Short FC suffix
        ]
        
        headers = self.get_random_headers()
        
        for pattern in url_patterns:
            test_url = f"{base_url}{pattern}"
            
            try:
                # Add delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                response = requests.get(test_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Parse the page to confirm it's the right team
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Check if the team name is in the title
                    title = soup.title.text if soup.title else ""
                    if team_name.lower() in title.lower():
                        logger.info(f"Found {team_name} on FBref: {test_url}")
                        
                        return {
                            'name': team_name,
                            'formatted_name': formatted_name,
                            'fbref_url': test_url,
                            'verified': True
                        }
            
            except Exception as e:
                logger.debug(f"Error checking {test_url}: {str(e)}")
        
        # If direct URL doesn't work, try searching
        search_url = f"https://fbref.com/en/search/search.fcgi?search={team_name.replace(' ', '+')}"
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for team links in search results
                team_links = soup.select('div.search-item-name a')
                
                for link in team_links:
                    if 'squads' in link['href'] and team_name.lower() in link.text.lower():
                        fbref_url = f"https://fbref.com{link['href']}"
                        logger.info(f"Found {team_name} through search: {fbref_url}")
                        
                        return {
                            'name': team_name,
                            'formatted_name': formatted_name,
                            'fbref_url': fbref_url,
                            'verified': True
                        }
        
        except Exception as e:
            logger.error(f"Error searching for {team_name}: {str(e)}")
        
        # If team not found, return unverified info
        logger.warning(f"Could not verify {team_name} on FBref")
        
        return {
            'name': team_name,
            'formatted_name': formatted_name,
            'fbref_url': None,
            'verified': False
        }
    
    def prepare_teams_for_fbref(self, teams_list):
        """
        Prepare a list of teams for FBref scraping
        
        Args:
            teams_list: List of team names or dictionaries
            
        Returns:
            List of team dictionaries with FBref info
        """
        logger.info(f"Preparing {len(teams_list)} teams for FBref scraping")
        
        prepared_teams = []
        
        for i, team in enumerate(teams_list):
            try:
                # Extract team name from either string or dictionary
                if isinstance(team, dict):
                    team_name = team['name']
                    team_id = team.get('id')
                    country = team.get('country')
                    league = team.get('league')
                else:
                    team_name = team
                    team_id = None
                    country = None
                    league = None
                
                logger.info(f"Processing team {i+1}/{len(teams_list)}: {team_name}")
                
                # Format and check on FBref
                formatted_name = self.format_team_name_for_fbref(team_name)
                fbref_info = self.check_team_on_fbref(team_name, formatted_name)
                
                # Create team info dictionary
                team_info = {
                    'id': team_id,
                    'name': team_name,
                    'country': country,
                    'league': league,
                    'formatted_name': fbref_info['formatted_name'],
                    'fbref_url': fbref_info['fbref_url'],
                    'verified': fbref_info['verified']
                }
                
                prepared_teams.append(team_info)
                
                # Add delay between requests
                if i < len(teams_list) - 1:
                    time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error processing {team}: {str(e)}")
        
        return prepared_teams
    
    def save_prepared_teams(self, teams, filename="fbref_teams.json"):
        """
        Save prepared teams to a JSON file
        
        Args:
            teams: List of prepared team dictionaries
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        # Group teams by verification status and league
        verified_teams = [t for t in teams if t['verified']]
        unverified_teams = [t for t in teams if not t['verified']]
        
        # Group verified teams by league
        teams_by_league = {}
        for team in verified_teams:
            league = team.get('league', 'Unknown League')
            if league not in teams_by_league:
                teams_by_league[league] = []
            teams_by_league[league].append(team)
        
        output = {
            'total_teams': len(teams),
            'verified_teams': len(verified_teams),
            'unverified_teams': len(unverified_teams),
            'teams_by_league': teams_by_league,
            'all_teams': teams,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save to file
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved {len(teams)} teams to {file_path}")
        return file_path

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FBref Team Preparation Tool')
    parser.add_argument('--source', choices=['files', 'database', 'both'], default='both',
                       help='Source for team names (files, database, or both)')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit the number of teams to process (0 for no limit)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify teams on FBref (slower but more accurate)')
    
    args = parser.parse_args()
    
    prep = FBrefTeamPreparation()
    
    teams_set = set()
    
    # Get teams from the specified sources
    if args.source in ['files', 'both']:
        file_teams = prep.extract_teams_from_matches()
        teams_set.update(file_teams)
        print(f"Extracted {len(file_teams)} teams from match files")
    
    if args.source in ['database', 'both']:
        db_teams = prep.get_teams_from_database()
        teams_set.update([team['name'] for team in db_teams])
        print(f"Extracted {len(db_teams)} teams from database")
    
    # Convert to list
    teams_list = list(teams_set)
    
    # Apply limit if specified
    if args.limit > 0:
        teams_list = teams_list[:args.limit]
    
    # Prepare teams for FBref
    if args.verify:
        prepared_teams = prep.prepare_teams_for_fbref(teams_list)
    else:
        # Just format names without verifying
        prepared_teams = [
            {
                'name': name,
                'formatted_name': prep.format_team_name_for_fbref(name),
                'fbref_url': None,
                'verified': False
            }
            for name in teams_list
        ]
    
    # Save prepared teams
    output_file = prep.save_prepared_teams(prepared_teams)
    
    print(f"\n=== FBref Team Preparation Summary ===")
    print(f"Total Teams: {len(prepared_teams)}")
    if args.verify:
        verified = [t for t in prepared_teams if t['verified']]
        print(f"Verified Teams: {len(verified)}")
        print(f"Unverified Teams: {len(prepared_teams) - len(verified)}")
    print(f"Output File: {output_file}")

if __name__ == "__main__":
    main()