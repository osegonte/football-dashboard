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
from dashboard.visualizations import DashboardVisualizations
from sqlalchemy import func
from database.db_setup import get_db_session
from database.models import Team, Match, League

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'development_key')

# Pipeline status tracking
pipeline_status = {
    "running": False,
    "last_run": None,
    "last_status": None,
    "progress": None
}

# Helper functions
def format_date(date_obj):
    """Format datetime object to display date"""
    if date_obj:
        return date_obj.strftime("%A, %d %B %Y")  # e.g., "Monday, 05 May 2025"
    return "Unknown Date"

# Database search operations
def search_teams(query):
    """Search teams by name or country
    
    Args:
        query: Search query string
        
    Returns:
        List of Team objects
    """
    session = get_db_session()
    try:
        like_query = f"%{query}%"
        teams = session.query(Team).filter(
            (Team.name.ilike(like_query)) | 
            (Team.country.ilike(like_query))
        ).order_by(Team.name).all()
        
        return teams
    finally:
        session.close()

def search_matches(query):
    """Search matches by team name, league, or venue
    
    Args:
        query: Search query string
        
    Returns:
        List of Match objects
    """
    session = get_db_session()
    try:
        like_query = f"%{query}%"
        matches = session.query(Match).filter(
            (Match.home_team_name.ilike(like_query)) | 
            (Match.away_team_name.ilike(like_query)) |
            (Match.venue.ilike(like_query))
        ).order_by(Match.match_date).all()
        
        # Also search by league name
        league_matches = session.query(Match).join(League).filter(
            League.name.ilike(like_query)
        ).order_by(Match.match_date).all()
        
        # Combine results (avoid duplicates)
        result = list(set(matches + league_matches))
        
        return result
    finally:
        session.close()

def search_leagues(query):
    """Search leagues by name or country
    
    Args:
        query: Search query string
        
    Returns:
        List of League objects
    """
    session = get_db_session()
    try:
        like_query = f"%{query}%"
        leagues = session.query(League).filter(
            (League.name.ilike(like_query)) | 
            (League.country.ilike(like_query))
        ).order_by(League.name).all()
        
        return leagues
    finally:
        session.close()

def get_league_by_id(league_id):
    """Get league by ID
    
    Args:
        league_id: League ID
        
    Returns:
        League object or None
    """
    session = get_db_session()
    try:
        return session.query(League).filter(League.id == league_id).first()
    finally:
        session.close()

def get_teams_by_league(league_id):
    """Get teams in a league
    
    Args:
        league_id: League ID
        
    Returns:
        List of Team objects
    """
    session = get_db_session()
    try:
        return session.query(Team).filter(Team.league_id == league_id).order_by(Team.name).all()
    finally:
        session.close()

def get_upcoming_matches_by_league(league_id, days=7):
    """Get upcoming matches in a league
    
    Args:
        league_id: League ID
        days: Number of days to look ahead
        
    Returns:
        List of Match objects
    """
    session = get_db_session()
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        matches = session.query(Match).filter(
            Match.league_id == league_id,
            func.date(Match.match_date) >= today,
            func.date(Match.match_date) <= end_date
        ).order_by(Match.match_date).all()
        
        return matches
    finally:
        session.close()

# Add methods to DBOperations
DBOperations.search_teams = search_teams
DBOperations.search_matches = search_matches
DBOperations.search_leagues = search_leagues
DBOperations.get_league_by_id = get_league_by_id
DBOperations.get_teams_by_league = get_teams_by_league
DBOperations.get_upcoming_matches_by_league = get_upcoming_matches_by_league

# Routes
@app.route('/')
def index():
    """Dashboard home page"""
    # Get upcoming matches
    matches = DBOperations.get_upcoming_matches(days=7)
    
    # Get current stats
    team_count = len(DBOperations.get_all_teams())
    league_count = len(DBOperations.get_all_leagues())
    match_count = len(matches)
    
    # Get teams with data
    teams = DBOperations.get_all_teams()
    teams_with_data = sum(1 for team in teams if team.team_data)
    
    # Data coverage percentage
    data_coverage = round((teams_with_data / team_count * 100) if team_count > 0 else 0, 1)
    
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
        teams_with_data=teams_with_data,
        data_coverage=data_coverage,
        pipeline_status=pipeline_status
    )

@app.route('/fixtures')
def fixtures():
    """Fixtures page displaying upcoming matches"""
    # Get filters from request
    days = request.args.get('days', default=7, type=int)
    selected_league = request.args.get('league', default=None, type=int)
    
    # Get leagues for filter
    leagues = DBOperations.get_all_leagues()
    
    # Get matches
    if selected_league:
        matches = DBOperations.get_upcoming_matches_by_league(selected_league, days=days)
    else:
        matches = DBOperations.get_upcoming_matches(days=days)
    
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
        selected_league=selected_league,
        days=days
    )

@app.route('/teams')
def teams():
    """Teams page displaying all teams"""
    # Get filters from request
    selected_league = request.args.get('league', default=None, type=int)
    
    # Get leagues for filter
    leagues = DBOperations.get_all_leagues()
    
    # Get teams
    if selected_league:
        teams_list = DBOperations.get_teams_by_league(selected_league)
    else:
        teams_list = DBOperations.get_all_teams()
    
    return render_template(
        'teams.html',
        teams=teams_list,
        leagues=leagues,
        selected_league=selected_league
    )

@app.route('/team/<int:team_id>')
def team_detail(team_id):
    """Team detail page with enhanced data display"""
    # Get team
    team = DBOperations.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'error')
        return redirect(url_for('teams'))
    
    # Get team matches
    matches = DBOperations.get_team_matches(team_id)
    
    # Get team data
    team_data = team.team_data if team.team_data else None
    
    # Team statistics (placeholder for now)
    team_stats = {
        'matches_played': len(matches.get('past', [])),
        'upcoming_matches': len(matches.get('future', [])),
        'in_league': team.league.name if team.league else 'Unknown League'
    }
    
    return render_template(
        'team_detail.html',
        team=team,
        team_data=team_data,
        team_stats=team_stats,
        past_matches=matches.get('past', []),
        future_matches=matches.get('future', [])
    )

@app.route('/run_pipeline', methods=['POST'])
def run_pipeline():
    """Run the data pipeline"""
    if pipeline_status["running"]:
        flash('Pipeline is already running', 'warning')
        return redirect(url_for('index'))
    
    # Start pipeline in a separate thread
    def run_pipeline_thread():
        pipeline_status["running"] = True
        pipeline_status["progress"] = "Starting pipeline..."
        
        try:
            runner = PipelineRunner()
            stats = runner.run_full_pipeline()
            
            pipeline_status["last_run"] = datetime.now()
            pipeline_status["last_status"] = "success"
            pipeline_status["progress"] = stats
        except Exception as e:
            pipeline_status["last_status"] = "error"
            pipeline_status["progress"] = str(e)
        finally:
            pipeline_status["running"] = False
    
    thread = threading.Thread(target=run_pipeline_thread)
    thread.daemon = True
    thread.start()
    
    flash('Pipeline started', 'success')
    return redirect(url_for('index'))

@app.route('/export_fixtures')
def export_fixtures():
    """Export fixtures as JSON"""
    days = request.args.get('days', default=7, type=int)
    matches = DBOperations.get_upcoming_matches(days=days)
    
    # Convert matches to dictionaries
    matches_data = []
    for match in matches:
        matches_data.append({
            'id': match.id,
            'external_id': match.external_id,
            'home_team': match.home_team_name,
            'away_team': match.away_team_name,
            'date': match.match_date.isoformat() if match.match_date else None,
            'time': match.start_time,
            'venue': match.venue,
            'league': match.league.name if match.league else 'Unknown League',
            'status': match.status
        })
    
    return jsonify(matches_data)

@app.route('/stats')
def stats():
    """Statistics dashboard page"""
    # Get data for charts and visualizations
    upcoming_matches = DBOperations.get_upcoming_matches(days=14)
    all_teams = DBOperations.get_all_teams()
    all_leagues = DBOperations.get_all_leagues()
    
    # Get visualizations data
    viz = DashboardVisualizations()
    
    # Matches by date
    matches_by_date = viz.get_matches_by_date(upcoming_matches, days=7)
    matches_by_date_data = viz.prepare_chart_data_for_matches_by_date(matches_by_date)
    
    # Matches by league
    matches_by_league = viz.get_matches_by_league(upcoming_matches, top_n=10)
    matches_by_league_data = viz.prepare_chart_data_for_leagues(matches_by_league)
    
    # Team stats
    team_stats = viz.get_team_stats(all_teams)
    team_coverage_data = viz.prepare_chart_data_for_team_coverage(team_stats)
    
    # Data coverage stats
    coverage_stats = viz.get_data_coverage_stats(all_teams, upcoming_matches)
    
    # Basic counts
    match_count = len(upcoming_matches)
    team_count = len(all_teams)
    league_count = len(all_leagues)
    
    return render_template(
        'stats.html',
        matches_by_date_data=matches_by_date_data,
        matches_by_league_data=matches_by_league_data,
        teams_by_league_data=team_stats['by_league'],
        teams_by_country_data=team_stats['by_country'],
        team_coverage_data=team_coverage_data,
        coverage_stats=coverage_stats,
        team_stats=team_stats,
        match_count=match_count,
        team_count=team_count,
        league_count=league_count,
        pipeline_status=pipeline_status
    )

@app.route('/search')
def search():
    """Search page for teams and matches"""
    query = request.args.get('q', '')
    
    results = {
        'teams': [],
        'matches': [],
        'leagues': []
    }
    
    if query and len(query) >= 2:
        # Search teams
        teams = DBOperations.search_teams(query)
        results['teams'] = teams
        
        # Search matches
        matches = DBOperations.search_matches(query)
        results['matches'] = matches
        
        # Search leagues
        leagues = DBOperations.search_leagues(query)
        results['leagues'] = leagues
    
    return render_template(
        'search.html',
        query=query,
        results=results,
        total_results=len(results['teams']) + len(results['matches']) + len(results['leagues'])
    )

@app.route('/league/<int:league_id>')
def league_detail(league_id):
    """League detail page"""
    # Get league
    league = DBOperations.get_league_by_id(league_id)
    if not league:
        flash('League not found', 'error')
        return redirect(url_for('fixtures'))
    
    # Get teams in this league
    teams = DBOperations.get_teams_by_league(league_id)
    
    # Get upcoming matches in this league
    upcoming_matches = DBOperations.get_upcoming_matches_by_league(league_id, days=30)
    
    # Group matches by date
    matches_by_date = {}
    for match in upcoming_matches:
        match_date = format_date(match.match_date)
        if match_date not in matches_by_date:
            matches_by_date[match_date] = []
        matches_by_date[match_date].append(match)
    
    return render_template(
        'league_detail.html',
        league=league,
        teams=teams,
        matches_by_date=matches_by_date,
        team_count=len(teams),
        match_count=len(upcoming_matches)
    )

# Filter for formatting dates in templates
@app.template_filter('date')
def date_filter(value):
    """Format date for display in templates"""
    if value:
        return value.strftime("%d %b %Y")
    return "Unknown"

@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime for display in templates"""
    if value:
        return value.strftime("%d %b %Y %H:%M")
    return "Unknown"

# JSON encoder for SQLAlchemy objects
@app.template_filter('tojson')
def tojson_filter(obj):
    """Convert object to JSON for use in JavaScript"""
    return json.dumps(obj)

# Context processor to add current date to all templates
@app.context_processor
def inject_now():
    """Add current datetime to template context"""
    return {'now': datetime.now()}

# Initialize the app
if __name__ == '__main__':
    app.run(debug=True)

@app.route('/guide')
def user_guide():
    """User Guide page"""
    return render_template('user_guide.html')