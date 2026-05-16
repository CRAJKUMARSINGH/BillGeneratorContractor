from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from database import get_session
from models import User
from auth_utils import SECRET_KEY, ALGORITHM

# auto_error=False: missing Authorization → None (open access via guest user)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def _guest_user(session: Session) -> User:
    user = session.exec(select(User).where(User.username == "guest")).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guest account not initialized",
        )
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Valid JWT → that user; missing or bad token → shared guest user (open access)."""
    if not token:
        return _guest_user(session)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return _guest_user(session)
    except InvalidTokenError:
        return _guest_user(session)

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        return _guest_user(session)
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user
