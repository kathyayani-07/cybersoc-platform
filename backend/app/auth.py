import hashlib
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuthSession, User
from app.time_utils import utc_now_naive

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = utc_now_naive() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_session(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
        expires_at=utc_now_naive() + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session)
    db.commit()
    return raw_token


def rotate_refresh_session(db: Session, raw_token: str) -> tuple[str, User] | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    session = (
        db.query(AuthSession)
        .filter(
            AuthSession.token_hash == token_hash,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > utc_now_naive(),
        )
        .first()
    )
    if session is None:
        return None

    now = utc_now_naive()
    claimed = db.query(AuthSession).filter(
        AuthSession.id == session.id,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > now,
    ).update({AuthSession.revoked_at: now}, synchronize_session=False)
    if claimed != 1:
        db.rollback()
        return None

    user = db.query(User).filter(User.id == session.user_id, User.is_active.is_(True)).first()
    if user is None:
        db.commit()
        return None

    replacement = secrets.token_urlsafe(48)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashlib.sha256(replacement.encode("utf-8")).hexdigest(),
            expires_at=utc_now_naive() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return replacement, user


def revoke_refresh_session(db: Session, raw_token: str) -> User | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    session = db.query(AuthSession).filter(AuthSession.token_hash == token_hash).first()
    if session is None:
        return None

    user = db.query(User).filter(User.id == session.user_id).first()
    if session.revoked_at is None:
        session.revoked_at = utc_now_naive()
        db.commit()
    return user


def get_user_from_access_token(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
    except JWTError:
        return None
    if not username:
        return None
    return db.query(User).filter(User.username == username, User.is_active.is_(True)).first()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = get_user_from_access_token(token, db)
    if user is None:
        raise credentials_exception
    return user


def get_optional_current_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User | None:
    return get_user_from_access_token(token, db)


def require_roles(*allowed_roles: str):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return dependency
