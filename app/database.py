"""
Database connection and session.

Schema source of truth: app.models. On startup, Base.metadata.create_all(bind=engine)
creates all tables and columns from the current models. For a new (empty) database,
no migration scripts need to be run. The scripts in scripts/ (migrate_*.py) are only
for existing databases that were created before a given column or table was added
to the models.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
