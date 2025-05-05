# Football Data Dashboard

A comprehensive dashboard for football (soccer) fixtures, team information, and statistics.

## Overview

The Football Data Dashboard is a web application built with Flask and SQLAlchemy that provides:

- Fixtures for upcoming football matches from multiple leagues
- Team information with detailed profiles
- League details and matches
- Interactive statistics and visualizations
- Search functionality across teams, leagues, and matches

The application scrapes data from SofaScore and other sources, processes it, and presents it in a user-friendly interface.

## Features

- **Match Scraper**: Collects upcoming match data using multiple fallback methods
- **Team Data Scraper**: Gathers detailed information about teams from Wikipedia, SofaScore, and other sources
- **Data Pipeline**: Automated ETL process to collect, process, and store football data
- **Web Dashboard**: Interactive interface to explore matches, teams, and leagues
- **Statistics**: Visualizations of match distribution, leagues, teams, and data coverage
- **Search**: Full-text search across all data in the system

## Installation

### Prerequisites

- Python 3.11+
- Virtual environment tool (venv, virtualenv)
- SQLite

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/football-dashboard.git
   cd football-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv_py311
   source venv_py311/bin/activate  # On Windows: venv_py311\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python main.py --init-db
   ```

5. Run the complete pipeline to fetch data:
   ```bash
   python main.py --all
   ```

## Usage

### Running the Application

To run the full application with data scraping, database processing, and web dashboard:

```bash
python main.py --all
```

The dashboard will be available at `http://localhost:5000`.

To run individual components:

```bash
# Initialize database only
python main.py --init-db

# Run data pipeline only
python main.py --run-pipeline

# Run pipeline with more days ahead
python main.py --run-pipeline --days 14

# Start dashboard only
python main.py --start-dashboard

# Start scheduler only
python main.py --start-scheduler
```

### Team Data Scraper

To run the team data scraper independently:

```bash
python scrapers/team_data_scraper.py --limit 20
```

Options:
- `--limit`: Maximum number of teams to scrape (default: 20)
- `--team-id` and `--team-name`: Scrape a specific team by ID and name

### Dashboard Navigation

The dashboard provides the following sections:

- **Home**: Overview of upcoming matches and dashboard statistics
- **Fixtures**: List of all upcoming matches with filtering options
- **Teams**: List of all teams with filtering by league
- **Stats**: Visualizations and statistics about matches, teams, and leagues
- **Search**: Search functionality for finding teams, leagues, and matches

## Project Structure

```
football-dashboard/
├── config.py                # Configuration settings
├── main.py                  # Main entry point
├── requirements.txt         # Dependencies
├── database/                # Database models and operations
│   ├── __init__.py
│   ├── db_setup.py          # Database initialization
│   ├── models.py            # SQLAlchemy models
│   └── operations.py        # Database operations
├── dashboard/               # Web dashboard
│   ├── __init__.py
│   ├── app.py               # Flask app
│   ├── routes.py            # Route handlers
│   ├── visualizations.py    # Visualization utilities
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── fixtures.html    # Fixtures page
│       └── ...
├── pipeline/                # Data pipeline
│   ├── __init__.py
│   ├── pipeline_runner.py   # Pipeline coordinator
│   └── scheduler.py         # Automated scheduler
└── scrapers/                # Data scrapers
    ├── __init__.py
    ├── daily_match_scraper.py    # Match scraper
    ├── team_data_scraper.py      # Team data scraper
    └── team_data_processor.py    # Team data processor
```

## Data Sources

The application collects data from multiple sources:

- **SofaScore**: Primary source for match fixtures
- **Wikipedia**: Team information, history, and details
- **Team Websites**: Additional team information
- **FBref**: Fallback source for match data

## Development

### Adding New Features

1. Create a virtual environment and install dependencies
2. Run the application with `--init-db` to set up the database
3. Make your changes to the codebase
4. Run the integration script to apply updates:
   ```bash
   python integrate_updates.py
   ```

### Common Issues

- **Module not found errors**: Make sure your virtual environment is activated
- **Chromedriver errors**: Update Chrome or reinstall the webdriver-manager
- **Port already in use**: Change the port in config.py or stop the process using port 5000

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data provided by SofaScore, Wikipedia, and FBref
- Icons by Font Awesome
- UI components by Bootstrap