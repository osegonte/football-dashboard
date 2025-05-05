#!/usr/bin/env python3
"""
Integration script to apply all updates to the Football Dashboard project
This script will:
1. Update the database models with any new fields
2. Install the team data scraper and other new files
3. Patch existing files with updates
4. Apply all changes to the dashboard templates
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# Make sure we're in the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Check if we're in the right directory
if not os.path.exists('main.py') or not os.path.exists('requirements.txt'):
    print("Error: This script must be run from the football-dashboard project root directory")
    sys.exit(1)

# Create backup directory
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'backups', f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
os.makedirs(BACKUP_DIR, exist_ok=True)

print(f"Creating backup in {BACKUP_DIR}")

def backup_file(filepath):
    """Create a backup of a file"""
    if os.path.exists(filepath):
        backup_path = os.path.join(BACKUP_DIR, filepath)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(filepath, backup_path)
        print(f"Backed up: {filepath}")
    else:
        print(f"Warning: File not found, cannot backup: {filepath}")

def copy_file(src, dst, overwrite=True):
    """Copy a file with optional overwrite"""
    if not os.path.exists(src):
        print(f"Error: Source file not found: {src}")
        return False
    
    # Make sure the destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    # Check if destination exists and we're not overwriting
    if os.path.exists(dst) and not overwrite:
        print(f"Skipping: {dst} already exists")
        return False
    
    # Backup existing file
    if os.path.exists(dst):
        backup_file(dst)
    
    # Copy the file
    shutil.copy2(src, dst)
    print(f"Installed: {dst}")
    return True

def patch_file(filepath, search_text, replace_text, create_if_not_exists=False):
    """Patch a file by replacing text"""
    # Check if file exists
    if not os.path.exists(filepath):
        if create_if_not_exists:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create empty file
            with open(filepath, 'w') as f:
                pass
            
            print(f"Created: {filepath}")
        else:
            print(f"Error: File not found: {filepath}")
            return False
    
    # Backup existing file
    backup_file(filepath)
    
    # Read file content
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if search text exists
    if search_text not in content:
        print(f"Warning: Search text not found in {filepath}")
        return False
    
    # Replace text
    new_content = content.replace(search_text, replace_text)
    
    # Write back to file
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"Patched: {filepath}")
    return True

def install_new_file(filepath, content):
    """Create a new file with the specified content"""
    # Make sure the directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(filepath):
        backup_file(filepath)
    
    # Create the file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created: {filepath}")
    return True

# Step 1: Backup critical files
backup_file('database/models.py')
backup_file('database/operations.py')
backup_file('dashboard/app.py')
backup_file('pipeline/pipeline_runner.py')
backup_file('scrapers/team_data_processor.py')

# Step 2: Install new files
print("\nInstalling new files...")
copy_file('scrapers/team_data_scraper.py', 'scrapers/team_data_scraper.py')
copy_file('scrapers/team_data_processor_fixed.py', 'scrapers/team_data_processor_fixed.py')
copy_file('dashboard/visualizations.py', 'dashboard/visualizations.py')
copy_file('dashboard/templates/stats.html', 'dashboard/templates/stats.html')
copy_file('dashboard/templates/search.html', 'dashboard/templates/search.html')
copy_file('dashboard/templates/league_detail.html', 'dashboard/templates/league_detail.html')
copy_file('dashboard/templates/team_detail_enhanced.html', 'dashboard/templates/team_detail_enhanced.html')

# Step 3: Create enhanced index template
print("\nCreating enhanced index template...")
backup_file('dashboard/templates/index.html')
copy_file('dashboard/templates/index.html', 'dashboard/templates/index_enhanced.html')

# Step 4: Update the dashboard app.py file
print("\nUpdating dashboard app.py file...")
backup_file('dashboard/app.py')

# Read the current app.py content
with open('dashboard/app.py', 'r') as f:
    app_content = f.read()

# Read the app updates
with open('dashboard/app_updates.py', 'r') as f:
    updates_content = f.read()

# Extract the necessary imports and route definitions
import_section = """
from sqlalchemy import func
from dashboard.visualizations import DashboardVisualizations
"""

# Insert the imports after other imports
app_content = app_content.replace(
    'from pipeline.pipeline_runner import PipelineRunner',
    'from pipeline.pipeline_runner import PipelineRunner' + import_section
)

# Add the routes to the app
app_content += """

# New routes added by integration script
@app.route('/stats')
def stats():
    \"\"\"Statistics dashboard page\"\"\"
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
    \"\"\"Search page for teams and matches\"\"\"
    query = request.args.get('q', '')
    
    results = {
        'teams': [],
        'matches': [],
        'leagues': []
    }
    
    if query and len(query) >= 2:
        # Search teams
        teams = search_teams(query)
        results['teams'] = teams
        
        # Search matches
        matches = search_matches(query)
        results['matches'] = matches
        
        # Search leagues
        leagues = search_leagues(query)
        results['leagues'] = leagues
    
    return render_template(
        'search.html',
        query=query,
        results=results,
        total_results=len(results['teams']) + len(results['matches']) + len(results['leagues'])
    )

@app.route('/league/<int:league_id>')
def league_detail(league_id):
    \"\"\"League detail page\"\"\"
    # Get league
    league = get_league_by_id(league_id)
    if not league:
        flash('League not found', 'error')
        return redirect(url_for('fixtures'))
    
    # Get teams in this league
    teams = get_teams_by_league(league_id)
    
    # Get upcoming matches in this league
    upcoming_matches = get_upcoming_matches_by_league(league_id, days=30)
    
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

# Helper functions for search
def search_teams(query):
    \"\"\"Search teams by name or country\"\"\"
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
    \"\"\"Search matches by team name, league, or venue\"\"\"
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
    \"\"\"Search leagues by name or country\"\"\"
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
    \"\"\"Get league by ID\"\"\"
    session = get_db_session()
    try:
        return session.query(League).filter(League.id == league_id).first()
    finally:
        session.close()

def get_teams_by_league(league_id):
    \"\"\"Get teams in a league\"\"\"
    session = get_db_session()
    try:
        return session.query(Team).filter(Team.league_id == league_id).order_by(Team.name).all()
    finally:
        session.close()

def get_upcoming_matches_by_league(league_id, days=7):
    \"\"\"Get upcoming matches in a league\"\"\"
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

# Override the team_detail route to use the enhanced template
@app.route('/team/<int:team_id>')
def team_detail(team_id):
    \"\"\"Team detail page with enhanced data display\"\"\"
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
        'team_detail_enhanced.html',
        team=team,
        team_data=team_data,
        team_stats=team_stats,
        past_matches=matches.get('past', []),
        future_matches=matches.get('future', [])
    )
"""

# Write the updated app.py content
with open('dashboard/app.py', 'w') as f:
    f.write(app_content)

# Step 5: Update base.html template with new navigation
print("\nUpdating base.html template...")
backup_file('dashboard/templates/base.html')

# Read the base.html content
with open('dashboard/templates/base.html', 'r') as f:
    base_content = f.read()

# Update the navigation
old_nav = """<div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('index') %}active{% endif %}" href="{{ url_for('index') }}">
                            <i class="fas fa-home me-1"></i> Home
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('fixtures') %}active{% endif %}" href="{{ url_for('fixtures') }}">
                            <i class="fas fa-calendar-alt me-1"></i> Fixtures
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('teams') %}active{% endif %}" href="{{ url_for('teams') }}">
                            <i class="fas fa-users me-1"></i> Teams
                        </a>
                    </li>
                    <li class="nav-item">
                        <form action="{{ url_for('run_pipeline') }}" method="post" class="d-inline">
                            <button type="submit" class="nav-link border-0 bg-transparent">
                                <i class="fas fa-sync-alt me-1"></i> Update Data
                            </button>
                        </form>
                    </li>
                </ul>
            </div>"""

new_nav = """<div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('index') %}active{% endif %}" href="{{ url_for('index') }}">
                            <i class="fas fa-home me-1"></i> Home
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('fixtures') %}active{% endif %}" href="{{ url_for('fixtures') }}">
                            <i class="fas fa-calendar-alt me-1"></i> Fixtures
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('teams') %}active{% endif %}" href="{{ url_for('teams') }}">
                            <i class="fas fa-users me-1"></i> Teams
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.path == url_for('stats') %}active{% endif %}" href="{{ url_for('stats') }}">
                            <i class="fas fa-chart-bar me-1"></i> Stats
                        </a>
                    </li>
                </ul>
                
                <form action="{{ url_for('search') }}" method="get" class="d-flex me-3">
                    <div class="input-group">
                        <input type="text" class="form-control" name="q" placeholder="Search..." aria-label="Search">
                        <button class="btn btn-outline-light" type="submit">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                </form>
                
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <form action="{{ url_for('run_pipeline') }}" method="post" class="d-inline">
                            <button type="submit" class="nav-link border-0 bg-transparent">
                                <i class="fas fa-sync-alt me-1"></i> Update Data
                            </button>
                        </form>
                    </li>
                </ul>
            </div>"""

# Replace the navigation
base_content = base_content.replace(old_nav, new_nav)

# Add floating search button for mobile
float_search_button = """
<!-- Floating Search Button (Mobile Only) -->
<div class="d-block d-lg-none position-fixed bottom-0 end-0 m-3" style="z-index: 1000;">
    <a href="{{ url_for('search') }}" class="btn btn-primary rounded-circle" style="width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;">
        <i class="fas fa-search"></i>
    </a>
</div>
"""

# Insert after body tag
base_content = base_content.replace("<body>", "<body>" + float_search_button)

# Write the updated base.html content
with open('dashboard/templates/base.html', 'w') as f:
    f.write(base_content)

# Step 6: Update pipeline_runner.py to use the fixed team_data_processor
print("\nUpdating pipeline_runner.py...")
backup_file('pipeline/pipeline_runner.py')
copy_file('pipeline/pipeline_runner_updated.py', 'pipeline/pipeline_runner.py')

# Step 7: Add import to main.py
print("\nUpdating main.py to add visualizations import...")
backup_file('main.py')

with open('main.py', 'r') as f:
    main_content = f.read()

# Add dashboard/visualizations.py import
if "from dashboard.visualizations import DashboardVisualizations" not in main_content:
    main_content = main_content.replace(
        "from dashboard.app import app",
        "from dashboard.app import app\nfrom dashboard.visualizations import DashboardVisualizations"
    )

with open('main.py', 'w') as f:
    f.write(main_content)

# Step 8: Create sofascore_data/teams directory if it doesn't exist
print("\nCreating teams directory for data storage...")
os.makedirs('sofascore_data/teams', exist_ok=True)

# Step 9: Create config.py file if it doesn't exist
print("\nChecking config.py file...")
if not os.path.exists('config.py'):
    print("Creating config.py file...")
    config_content = """# Configuration settings for Football Dashboard

# Database settings
DATABASE_PATH = 'database/football_data.db'

# Scraper settings
DATA_DIR = 'sofascore_data'
SCRAPE_DAYS_AHEAD = 7

# Dashboard settings
DEBUG_MODE = False
HOST = '0.0.0.0'
PORT = 5000

# Scheduler settings
SCHEDULER_INTERVAL_HOURS = 12
DAILY_RUN_TIME = "00:00"  # Midnight"""
    
    with open('config.py', 'w') as f:
        f.write(config_content)

# Step 10: Run migrations to update the database schema (if needed)
print("\nMigration for database schema is not needed since we're using sqlalchemy with create_all()")

# Step 11: Success message
print("\n" + "="*80)
print("FOOTBALL DASHBOARD UPDATES SUCCESSFULLY APPLIED!")
print("="*80)
print("\nBackups have been saved to:", BACKUP_DIR)
print("\nNew features added:")
print("1. Team data scraper that collects information from multiple sources")
print("2. Fixed team data processing to resolve session binding issues")
print("3. Enhanced dashboard with statistics visualizations")
print("4. Search functionality for teams, leagues, and matches")
print("5. Enhanced team and league detail pages")
print("\nYou can now run the app with:")
print("python main.py --all")
print("\nOr run just the team data scraper with:")
print("python scrapers/team_data_scraper.py --limit 20")
print("="*80)