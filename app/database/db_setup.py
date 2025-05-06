import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

class DatabaseManager:
    """Database manager for creating and managing the SQLite database"""
    
    def __init__(self, db_path='database/football_data.db'):
        """Initialize the database manager
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create SQLite database engine
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Create session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def init_db(self):
        """Initialize the database by creating all tables"""
        Base.metadata.create_all(self.engine)
        print("Database initialized successfully")
    
    def get_session(self):
        """Get a new database session
        
        Returns:
            SQLAlchemy session object
        """
        return self.Session()
    
    def close_session(self, session):
        """Close a database session
        
        Args:
            session: SQLAlchemy session to close
        """
        session.close()


# Default database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get a database session from the default manager
    
    Returns:
        SQLAlchemy session object
    """
    return db_manager.get_session()

def init_database():
    """Initialize the database with the default manager"""
    db_manager.init_db()