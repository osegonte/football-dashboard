from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Association table for many-to-many relationship between Team and Match
team_match = Table(
    'team_match',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
    Column('match_id', Integer, ForeignKey('matches.id'), primary_key=True),
    Column('is_home', Boolean, default=False),  # Whether the team is home or away
)

class Team(Base):
    """Team model to store information about football teams"""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    country = Column(String(100))
    league_id = Column(Integer, ForeignKey('leagues.id'))
    logo_url = Column(String(255))
    external_id = Column(String(50), unique=True)  # ID from external source (SofaScore)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="teams")
    matches = relationship("Match", secondary=team_match, back_populates="teams")
    
    # Additional team metadata
    team_data = relationship("TeamData", back_populates="team", uselist=False)
    
    def __repr__(self):
        return f"<Team(name='{self.name}', country='{self.country}')>"

class Match(Base):
    """Match model to store football fixtures/matches"""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True)  # ID from SofaScore
    home_team_name = Column(String(100), nullable=False)
    away_team_name = Column(String(100), nullable=False)
    match_date = Column(DateTime)
    start_time = Column(String(10))
    status = Column(String(50))
    venue = Column(String(100))
    round = Column(String(50))
    league_id = Column(Integer, ForeignKey('leagues.id'))
    source = Column(String(50))  # Where the data came from (api, browser, fbref)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="matches")
    teams = relationship("Team", secondary=team_match, back_populates="matches")
    
    def __repr__(self):
        return f"<Match('{self.home_team_name}' vs '{self.away_team_name}', date='{self.match_date}')>"

class League(Base):
    """League model to store football leagues/competitions"""
    __tablename__ = 'leagues'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    country = Column(String(100))
    external_id = Column(String(50), unique=True)  # ID from external source
    
    # Relationships
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")
    
    def __repr__(self):
        return f"<League(name='{self.name}', country='{self.country}')>"

class TeamData(Base):
    """Team data model to store additional information about teams"""
    __tablename__ = 'team_data'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), unique=True)
    stadium = Column(String(100))
    manager = Column(String(100))
    founded = Column(Integer)
    website = Column(String(255))
    description = Column(Text)
    last_scraped = Column(DateTime)
    
    # Relationships
    team = relationship("Team", back_populates="team_data")
    
    def __repr__(self):
        return f"<TeamData(team_id={self.team_id}, last_scraped='{self.last_scraped}')>"