import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import Session, engine, create_db_and_tables
from backend.models import User
from backend.auth_utils import get_password_hash
from sqlmodel import select

def seed_rajkumar():
    # Ensure tables exist
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if user already exists
        statement = select(User).where(User.username == "rajkumar")
        user = session.exec(statement).first()
        
        if user:
            print(f"User 'rajkumar' already exists. Updating password...")
            user.hashed_password = get_password_hash("rajkumar")
        else:
            print(f"Creating user 'rajkumar'...")
            user = User(
                username="rajkumar",
                hashed_password=get_password_hash("rajkumar"),
                role="admin"  # Giving admin role to the primary user
            )
            session.add(user)
        
        session.commit()
        print("Success: User 'rajkumar' is ready with password 'rajkumar'.")

if __name__ == "__main__":
    seed_rajkumar()
