import os
from sqlmodel import SQLModel, create_engine, Session

# Check for environment variable (Production)
database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Fix for Heroku/Render using postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Postgres Connection
    engine = create_engine(database_url, echo=False)
else:
    # Local Development
    sqlite_file_name = "database.db"
    database_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
