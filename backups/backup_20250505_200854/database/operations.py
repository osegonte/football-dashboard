import datetime
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .db_setup import get_db_session
from .models import Team, Match, League, TeamData, team_match

class DBOperations:
    """Class to handle database operations"""
    
    @staticmethod
    def upsert_league(name, country=None, external_id=None):
        """Insert or update a league
        
        Args:
            name: League name
            country: League country
            external_id: External ID for the league
            
        Returns:
            League object
        """
        session = get_db_session()
        try:
            # Try to find existing league by name
            league = session.query(League).filter(func.lower(League.name) == func.lower(name)).first()
            
            if league:
                # Update existing league
                if country and not league.country:
                    league.country = country
                if external_id and not league.external_id:
                    league.external_id = external_id
            else:
                # Create new league
                league = League(name=name, country=country, external_id=external_id)
                session.add(league)
            
            session.commit()
            return league
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @staticmethod
    def upsert_team(name, country=None, league_id=None, external_id=None, logo_url=None):
        """Insert or update a team
        
        Args:
            name: Team name
            country: Team country
            league_id: League ID
            external_id: External ID for the team
            logo_url: URL to team logo
            
        Returns:
            Team object
        """
        session = get_db_session()
        try:
            # Try to find existing team by name
            team = session.query(Team).filter(func.lower(Team.name) == func.lower(name)).first()
            
            if team:
                # Update existing team
                if country and not team.country:
                    team.country = country
                if league_id and not team.league_id:
                    team.league_id = league_id
                if external_id and not team.external_id:
                    team.external_id = external_id
                if logo_url and not team.logo_url:
                    team.logo_url = logo_url
                
                # Update last_updated timestamp
                team.last_updated = datetime.datetime.utcnow()
            else:
                # Create new team
                team = Team(
                    name=name,
                    country=country,
                    league_id=league_id,
                    external_id=external_id,
                    logo_url=logo_url,
                    last_updated=datetime.datetime.utcnow()
                )
                session.add(team)
            
            session.commit()
            return team
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @staticmethod
    def upsert_match(external_id, home_team_name, away_team_name, match_date, 
                    league_id=None, start_time=None, status=None, venue=None, 
                    round=None, source=None):
        """Insert or update a match
        
        Args:
            external_id: External ID for the match
            home_team_name: Home team name
            away_team_name: Away team name
            match_date: Match date
            league_id: League ID
            start_time: Match start time
            status: Match status
            venue: Match venue
            round: Match round/stage
            source: Data source
            
        Returns:
            Match object
        """
        session = get_db_session()
        try:
            # Try to find existing match by external_id
            match = session.query(Match).filter(Match.external_id == external_id).first()
            
            if match:
                # Update existing match
                match.home_team_name = home_team_name
                match.away_team_name = away_team_name
                match.match_date = match_date
                if league_id:
                    match.league_id = league_id
                if start_time:
                    match.start_time = start_time
                if status:
                    match.status = status
                if venue:
                    match.venue = venue
                if round:
                    match.round = round
                if source:
                    match.source = source
                
                # Update last_updated timestamp
                match.last_updated = datetime.datetime.utcnow()
            else:
                # Create new match
                match = Match(
                    external_id=external_id,
                    home_team_name=home_team_name,
                    away_team_name=away_team_name,
                    match_date=match_date,
                    league_id=league_id,
                    start_time=start_time,
                    status=status,
                    venue=venue,
                    round=round,
                    source=source,
                    last_updated=datetime.datetime.utcnow()
                )
                session.add(match)
            
            session.commit()
            return match
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @staticmethod
    def link_team_to_match(team_id, match_id, is_home):
        """Link a team to a match
        
        Args:
            team_id: Team ID
            match_id: Match ID
            is_home: Whether the team is the home team
            
        Returns:
            True if successful, False otherwise
        """
        session = get_db_session()
        try:
            # Check if link already exists
            exists = session.query(team_match).filter_by(
                team_id=team_id, match_id=match_id
            ).first() is not None
            
            if not exists:
                # Create association
                session.execute(team_match.insert().values(
                    team_id=team_id,
                    match_id=match_id,
                    is_home=is_home
                ))
                session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            print(f"Error linking team to match: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def upsert_team_data(team_id, stadium=None, manager=None, founded=None, 
                        website=None, description=None):
        """Insert or update team data
        
        Args:
            team_id: Team ID
            stadium: Team stadium
            manager: Team manager
            founded: Year founded
            website: Team website
            description: Team description
            
        Returns:
            TeamData object
        """
        session = get_db_session()
        try:
            # Try to find existing team data
            team_data = session.query(TeamData).filter(TeamData.team_id == team_id).first()
            
            if team_data:
                # Update existing team data
                if stadium:
                    team_data.stadium = stadium
                if manager:
                    team_data.manager = manager
                if founded:
                    team_data.founded = founded
                if website:
                    team_data.website = website
                if description:
                    team_data.description = description
                
                # Update last_scraped timestamp
                team_data.last_scraped = datetime.datetime.utcnow()
            else:
                # Create new team data
                team_data = TeamData(
                    team_id=team_id,
                    stadium=stadium,
                    manager=manager,
                    founded=founded,
                    website=website,
                    description=description,
                    last_scraped=datetime.datetime.utcnow()
                )
                session.add(team_data)
            
            session.commit()
            return team_data
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @staticmethod
    def get_upcoming_matches(days=7):
        """Get upcoming matches
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of Match objects
        """
        session = get_db_session()
        try:
            today = datetime.datetime.now().date()
            end_date = today + datetime.timedelta(days=days)
            
            matches = session.query(Match).filter(
                func.date(Match.match_date) >= today,
                func.date(Match.match_date) <= end_date
            ).order_by(Match.match_date).all()
            
            return matches
        finally:
            session.close()
    
    @staticmethod
    def get_teams_needing_data(limit=50):
        """Get teams that need additional data
        
        Args:
            limit: Maximum number of teams to return
            
        Returns:
            List of Team objects
        """
        session = get_db_session()
        try:
            # Get teams with either no team_data or old team_data
            subquery = session.query(TeamData.team_id)
            teams = session.query(Team).filter(
                ~Team.id.in_(subquery)
            ).limit(limit).all()
            
            return teams
        finally:
            session.close()
    
    @staticmethod
    def get_match_by_id(match_id):
        """Get match by ID
        
        Args:
            match_id: Match ID
            
        Returns:
            Match object or None
        """
        session = get_db_session()
        try:
            return session.query(Match).filter(Match.id == match_id).first()
        finally:
            session.close()
    
    @staticmethod
    def get_team_by_id(team_id):
        """Get team by ID
        
        Args:
            team_id: Team ID
            
        Returns:
            Team object or None
        """
        session = get_db_session()
        try:
            return session.query(Team).filter(Team.id == team_id).first()
        finally:
            session.close()
    
    @staticmethod
    def get_team_matches(team_id, past=True, future=True, limit=10):
        """Get matches for a team
        
        Args:
            team_id: Team ID
            past: Include past matches
            future: Include future matches
            limit: Maximum number of matches per category
            
        Returns:
            Dictionary with past and future matches
        """
        session = get_db_session()
        try:
            today = datetime.datetime.now().date()
            result = {"past": [], "future": []}
            
            # Get team
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return result
            
            # Get match IDs for this team
            match_ids = session.query(team_match.c.match_id).filter(
                team_match.c.team_id == team_id
            ).all()
            match_ids = [m[0] for m in match_ids]
            
            if past:
                # Get past matches
                past_matches = session.query(Match).filter(
                    Match.id.in_(match_ids),
                    func.date(Match.match_date) < today
                ).order_by(Match.match_date.desc()).limit(limit).all()
                result["past"] = past_matches
            
            if future:
                # Get future matches
                future_matches = session.query(Match).filter(
                    Match.id.in_(match_ids),
                    func.date(Match.match_date) >= today
                ).order_by(Match.match_date).limit(limit).all()
                result["future"] = future_matches
            
            return result
        finally:
            session.close()
    
    @staticmethod
    def get_all_leagues():
        """Get all leagues
        
        Returns:
            List of League objects
        """
        session = get_db_session()
        try:
            return session.query(League).order_by(League.name).all()
        finally:
            session.close()
    
    @staticmethod
    def get_all_teams():
        """Get all teams
        
        Returns:
            List of Team objects
        """
        session = get_db_session()
        try:
            return session.query(Team).order_by(Team.name).all()
        finally:
            session.close()