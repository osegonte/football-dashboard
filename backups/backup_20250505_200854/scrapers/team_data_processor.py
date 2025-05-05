import os
import csv
import json
from datetime import datetime
import pandas as pd
from database.operations import DBOperations
from database.models import Team, Match, League

class TeamDataProcessor:
    """
    Process match data to extract and store team information
    """
    
    def __init__(self, data_dir="sofascore_data"):
        """
        Initialize the team data processor
        
        Args:
            data_dir: Directory containing match data files
        """
        self.data_dir = data_dir
        self.daily_dir = os.path.join(self.data_dir, "daily")
        self.processed_teams = set()  # Track processed teams to avoid duplicates
    
    def process_match_file(self, file_path):
        """
        Process a match CSV file to extract teams
        
        Args:
            file_path: Path to the CSV file with match data
            
        Returns:
            Dictionary with statistics about processed data
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return {"matches": 0, "teams": 0, "leagues": 0}
        
        stats = {"matches": 0, "teams": 0, "leagues": 0}
        teams_added = set()
        leagues_added = set()
        
        try:
            # Read the match data
            matches_df = pd.read_csv(file_path)
            
            # Process each match
            for _, match in matches_df.iterrows():
                # Extract match data
                match_id = str(match.get('id', ''))
                external_id = match_id if match_id else f"generated-{hash(match['home_team'] + match['away_team'] + str(match.get('date', '')))}"
                
                # Get or create league
                league_name = match.get('league', 'Unknown League')
                country = match.get('country', None)
                
                league = DBOperations.upsert_league(
                    name=league_name,
                    country=country
                )
                
                if league.name not in leagues_added:
                    leagues_added.add(league.name)
                    stats["leagues"] += 1
                
                # Process match date
                match_date = None
                date_str = match.get('date', '')
                if date_str:
                    try:
                        match_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            match_date = datetime.strptime(date_str, "%Y/%m/%d")
                        except ValueError:
                            print(f"Could not parse date: {date_str}")
                
                # Add or update match in database
                db_match = DBOperations.upsert_match(
                    external_id=external_id,
                    home_team_name=match['home_team'],
                    away_team_name=match['away_team'],
                    match_date=match_date,
                    league_id=league.id,
                    start_time=match.get('start_time', None),
                    status=match.get('status', None),
                    venue=match.get('venue', None),
                    round=match.get('round', None),
                    source=match.get('source', None)
                )
                
                stats["matches"] += 1
                
                # Process home team
                home_team = DBOperations.upsert_team(
                    name=match['home_team'],
                    country=country,
                    league_id=league.id
                )
                
                if home_team.name not in teams_added and home_team.name not in self.processed_teams:
                    teams_added.add(home_team.name)
                    self.processed_teams.add(home_team.name)
                    stats["teams"] += 1
                
                # Process away team
                away_team = DBOperations.upsert_team(
                    name=match['away_team'],
                    country=country,
                    league_id=league.id
                )
                
                if away_team.name not in teams_added and away_team.name not in self.processed_teams:
                    teams_added.add(away_team.name)
                    self.processed_teams.add(away_team.name)
                    stats["teams"] += 1
                
                # Link teams to match
                DBOperations.link_team_to_match(home_team.id, db_match.id, is_home=True)
                DBOperations.link_team_to_match(away_team.id, db_match.id, is_home=False)
            
            return stats
            
        except Exception as e:
            print(f"Error processing match file {file_path}: {str(e)}")
            return {"matches": 0, "teams": 0, "leagues": 0}
    
    def process_all_match_files(self):
        """
        Process all match files in the daily directory
        
        Returns:
            Dictionary with statistics about processed data
        """
        if not os.path.exists(self.daily_dir):
            print(f"Daily directory not found: {self.daily_dir}")
            return {"files": 0, "matches": 0, "teams": 0, "leagues": 0}
        
        stats = {"files": 0, "matches": 0, "teams": 0, "leagues": 0}
        
        for filename in os.listdir(self.daily_dir):
            if filename.endswith('.csv') and filename.startswith('matches_'):
                file_path = os.path.join(self.daily_dir, filename)
                
                print(f"Processing {filename}...")
                file_stats = self.process_match_file(file_path)
                
                stats["files"] += 1
                stats["matches"] += file_stats["matches"]
                stats["teams"] += file_stats["teams"]
                stats["leagues"] += file_stats["leagues"]
        
        return stats
    
    def get_team_list_for_scraper(self, output_file='teams_to_scrape.json'):
        """
        Generate a list of teams that need additional data
        
        Args:
            output_file: Path to output JSON file
            
        Returns:
            Number of teams written to file
        """
        # Get teams that need additional data
        teams = DBOperations.get_teams_needing_data(limit=100)
        
        team_list = []
        for team in teams:
            team_info = {
                'id': team.id,
                'name': team.name,
                'league': team.league.name if team.league else 'Unknown League',
                'country': team.country if team.country else 'Unknown'
            }
            team_list.append(team_info)
        
        # Write to file
        output_path = os.path.join(self.data_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(team_list, f, indent=2)
        
        print(f"✓ Wrote {len(team_list)} teams to {output_path}")
        return len(team_list)