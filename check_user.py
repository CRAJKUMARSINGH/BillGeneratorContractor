import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.database import Session, engine
    from backend.models import User
    from sqlmodel import select

    def check_user(username):
        with Session(engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if user:
                print(f"User '{username}' found.")
            else:
                print(f"User '{username}' NOT found.")

    if __name__ == "__main__":
        check_user("rajkumar")
except Exception as e:
    print(f"Error checking user: {e}")
