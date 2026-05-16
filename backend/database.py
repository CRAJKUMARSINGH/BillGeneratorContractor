import os
from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

DATABASE_URL = os.getenv("DATABASE_URL", sqlite_url)

# SQLModel expects connect_args for sqlite to not restrict threads
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

_engine_kw = {"echo": False, "connect_args": connect_args}
if "sqlite" not in DATABASE_URL:
    _engine_kw["pool_size"] = 10
    _engine_kw["max_overflow"] = 20
engine = create_engine(DATABASE_URL, **_engine_kw)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
