from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import sys
import json
from datetime import datetime, timedelta
import threading

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.operations import DBOperations
from pipeline.pipeline_runner import PipelineRunner

app = Flask(__name__)
app.secret_key = 'football_dashboard_secret_key'  # For flash messages

# Global variables for pipeline status
pipeline_status = {
    "running": False,
    "last_run": None,
    "stats": None
}

def format_date(date_obj):
    """Format date for display"""
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d")

def format_datetime(date_obj):
    """Format datetime for display"""
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d %H:%M")

@app.template_filter('date')
def date_filter(date_obj):
    """Template filter for dates"""
    return format_date(date_obj)

@app.template_filter('datetime')
def datetime_filter(date_obj):
    """Template filter for datetimes"""
    return format_datetime(date_obj)

def run_pipeline_async():
    """Run the pipeline in a separate thread"""
    global pipeline_status
    
    try:
        pipeline_status["running"] = True
        
        # Run the pipeline
        runner = PipelineRunner()
        stats = runner.run_full_pipeline()
        
        # Update status
        pipeline_status["last_run"] = datetime.now()
        pipeline_status["stats"] = stats
        pipeline_status["running"] = False
        
    except Exception as e:
        pipeline_status["running"] = False
        pipeline_status["error"] = str(e)

@app.route('/')
def index():
    """Dashboard home page"""
    # Get upcoming matches
    matches = DBOperations.get_upcoming_matches(days=7)
    
    # Get current stats
    team_count = len(DBOperations.get_all_teams())
    league_count = len(DBOperations.get_all_leagues())
    match_count = len(matches)
    
    # Group matches by date
    matches_by_date = {}
    for match in matches:
        match_date = format_date(match.match_date)
        if match_date not in matches_by_date:
            matches_by_date[match_date] = []
        matches_by_date[match_date].append(match)
    
    return render_template(
        'index.html',
        matches_by_date=matches_by_date,
        team_count=team_count,
        league_count=league_count,
        match_count=match_count,
        pipeline_status=pipeline_status
    )

@app.route('/fixtures')
def fixtures():
    """Fixtures page"""
    # Get filter parameters
    days = request.args.get('days', 7, type=int)
    league_id = request.args.get('league', None, type=int)
    
    # Get upcoming matches
    matches = DBOperations.get_upcoming_matches(days=days)
    
    # Filter by league if specified
    if league_id:
        matches = [m for m in matches if m.league_id == league_id]
    
    # Get leagues for filter dropdown
    leagues = DBOperations.get_all_leagues()
    
    # Group matches by date
    matches_by_date = {}
    for match in matches:
        match_date = format_date(match.match_date)
        if match_date not in matches_by_date:
            matches_by_date[match_date] = []
        matches_by_date[match_date].append(match)
    
    return render_template(
        'fixtures.html',
        matches_by_date=matches_by_date,
        leagues=leagues,
        selected_league=league_id,
        days=days
    )

@app.route('/teams')
def teams():
    """Teams page"""
    # Get teams
    all_teams = DBOperations.get_all_teams()
    
    # Get filter parameters
    league_id = request.args.get('league', None, type=int)
    
    # Filter by league if specified
    if league_id:
        teams_list = [t for t in all_teams if t.league_id == league_id]
    else:
        teams_list = all_teams
    
    # Get leagues for filter dropdown
    leagues = DBOperations.get_all_leagues()
    
    return render_template(
        'teams.html',
        teams=teams_list,
        leagues=leagues,
        selected_league=league_id
    )

@app.route('/team/<int:team_id>')
def team_detail(team_id):
    """Team detail page"""
    # Get team
    team = DBOperations.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'error')
        return redirect(url_for('teams'))
    
    # Get team matches
    matches = DBOperations.get_team_matches(team_id)
    
    # Get team data
    team_data = team.team_data if team.team_data else None
    
    return render_template(
        'team_detail.html',
        team=team,
        team_data=team_data,
        past_matches=matches.get('past', []),
        future_matches=matches.get('future', [])
    )

@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    """Run the pipeline"""
    global pipeline_status
    
    if pipeline_status["running"]:
        flash('Pipeline is already running', 'warning')
        return redirect(url_for('index'))
    
    # Start pipeline in a separate thread
    thread = threading.Thread(target=run_pipeline_async)
    thread.daemon = True
    thread.start()
    
    flash('Pipeline started', 'success')
    return redirect(url_for('index'))

@app.route('/pipeline-status')
def get_pipeline_status():
    """Get current pipeline status as JSON"""
    global pipeline_status
    
    status_copy = pipeline_status.copy()
    if status_copy["last_run"]:
        status_copy["last_run"] = status_copy["last_run"].strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify(status_copy)

@app.route('/export-teams')
def export_teams():
    """Export teams data to JSON"""
    # Get teams
    all_teams = DBOperations.get_all_teams()
    
    # Convert teams to JSON-serializable format
    teams_list = []
    for team in all_teams:
        team_data = {
            'id': team.id,
            'name': team.name,
            'league': team.league.name if team.league else 'Unknown League',
            'country': team.country if team.country else 'Unknown',
            'has_team_data': bool(team.team_data)
        }
        teams_list.append(team_data)
    
    return jsonify(teams_list)

@app.route('/export-fixtures')
def export_fixtures():
    """Export fixture data to JSON"""
    # Get upcoming matches
    matches = DBOperations.get_upcoming_matches(days=14)
    
    # Convert matches to JSON-serializable format
    fixtures_list = []
    for match in matches:
        fixture_data = {
            'id': match.id,
            'home_team': match.home_team_name,
            'away_team': match.away_team_name,
            'match_date': format_date(match.match_date),
            'start_time': match.start_time,
            'league': match.league.name if match.league else 'Unknown League',
            'venue': match.venue if match.venue else 'Unknown'
        }
        fixtures_list.append(fixture_data)
    
    return jsonify(fixtures_list)

def main():
    """Main function to run the Flask app"""
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()