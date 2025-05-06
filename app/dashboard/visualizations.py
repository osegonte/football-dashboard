import os
import pandas as pd
import json
from datetime import datetime, timedelta

class DashboardVisualizations:
    """
    Generate data for dashboard visualizations
    """
    
    @staticmethod
    def get_matches_by_date(matches, days=7):
        """
        Group matches by date for charts
        
        Args:
            matches: List of Match objects
            days: Number of days to look ahead
            
        Returns:
            Dictionary with dates and match counts
        """
        # Create date range
        today = datetime.now().date()
        dates = [today + timedelta(days=i) for i in range(days)]
        
        # Initialize counts
        matches_by_date = {date.strftime('%Y-%m-%d'): 0 for date in dates}
        
        # Count matches per date
        for match in matches:
            if match.match_date:
                date_str = match.match_date.strftime('%Y-%m-%d')
                if date_str in matches_by_date:
                    matches_by_date[date_str] += 1
        
        return matches_by_date
    
    @staticmethod
    def get_matches_by_league(matches, top_n=10):
        """
        Count matches by league for charts
        
        Args:
            matches: List of Match objects
            top_n: Number of top leagues to return
            
        Returns:
            Dictionary with league names and match counts
        """
        matches_by_league = {}
        
        for match in matches:
            league_name = match.league.name if match.league else 'Unknown League'
            if league_name in matches_by_league:
                matches_by_league[league_name] += 1
            else:
                matches_by_league[league_name] = 1
        
        # Sort by count and get top N
        sorted_leagues = sorted(matches_by_league.items(), key=lambda x: x[1], reverse=True)
        top_leagues = sorted_leagues[:top_n]
        
        return dict(top_leagues)
    
    @staticmethod
    def get_team_stats(teams):
        """
        Generate team statistics for charts
        
        Args:
            teams: List of Team objects
            
        Returns:
            Dictionary with team statistics
        """
        teams_by_league = {}
        teams_by_country = {}
        teams_with_data = 0
        
        for team in teams:
            # Count by league
            league_name = team.league.name if team.league else 'Unknown League'
            if league_name in teams_by_league:
                teams_by_league[league_name] += 1
            else:
                teams_by_league[league_name] = 1
            
            # Count by country
            country = team.country if team.country else 'Unknown'
            if country in teams_by_country:
                teams_by_country[country] += 1
            else:
                teams_by_country[country] = 1
            
            # Count teams with additional data
            if team.team_data:
                teams_with_data += 1
        
        # Sort by count and get top 10
        top_leagues = dict(sorted(teams_by_league.items(), key=lambda x: x[1], reverse=True)[:10])
        top_countries = dict(sorted(teams_by_country.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'by_league': top_leagues,
            'by_country': top_countries,
            'with_data': teams_with_data,
            'without_data': len(teams) - teams_with_data
        }
    
    @staticmethod
    def get_data_coverage_stats(teams, matches):
        """
        Calculate data coverage statistics
        
        Args:
            teams: List of Team objects
            matches: List of Match objects
            
        Returns:
            Dictionary with coverage statistics
        """
        total_teams = len(teams)
        teams_with_data = sum(1 for team in teams if team.team_data)
        
        total_matches = len(matches)
        matches_with_venue = sum(1 for match in matches if match.venue)
        
        coverage = {
            'team_data_coverage': {
                'value': round((teams_with_data / total_teams * 100) if total_teams > 0 else 0, 1),
                'total': total_teams,
                'covered': teams_with_data
            },
            'match_venue_coverage': {
                'value': round((matches_with_venue / total_matches * 100) if total_matches > 0 else 0, 1),
                'total': total_matches,
                'covered': matches_with_venue
            }
        }
        
        return coverage
    
    @staticmethod
    def prepare_chart_data_for_matches_by_date(matches_by_date):
        """
        Prepare data for matches by date chart (React component)
        
        Args:
            matches_by_date: Dictionary with dates and match counts
            
        Returns:
            List of data points for chart
        """
        chart_data = []
        
        for date_str, count in matches_by_date.items():
            # Format date for display
            display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%a, %b %d')
            
            chart_data.append({
                'date': display_date,
                'matches': count
            })
        
        return chart_data
    
    @staticmethod
    def prepare_chart_data_for_leagues(matches_by_league):
        """
        Prepare data for leagues chart (React component)
        
        Args:
            matches_by_league: Dictionary with league names and match counts
            
        Returns:
            List of data points for chart
        """
        chart_data = []
        
        for league, count in matches_by_league.items():
            chart_data.append({
                'name': league,
                'matches': count
            })
        
        return chart_data
    
    @staticmethod
    def prepare_chart_data_for_team_coverage(team_stats):
        """
        Prepare data for team coverage chart (React component)
        
        Args:
            team_stats: Dictionary with team statistics
            
        Returns:
            List of data points for chart
        """
        return [
            {'name': 'With Data', 'value': team_stats['with_data']},
            {'name': 'Without Data', 'value': team_stats['without_data']}
        ]