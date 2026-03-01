from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt import InvalidTokenError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import settings

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Retrieve the current user's ID from HTTP Bearer authorization credentials.
    
    Extracts the JWT from the provided HTTPAuthorizationCredentials and returns the `sub` claim value (user id) after validation.
    
    Returns:
        str: The user id extracted from the token.
    """
    token = credentials.credentials
    return _decode_token(token)


def _decode_token(token: str) -> str:
    """
    Decode and validate a JWT and extract its subject claim as the user id.
    
    Parameters:
        token (str): JWT string containing a "sub" claim.
    
    Returns:
        user_id (str): The subject ("sub") claim from the token as a string.
    
    Raises:
        HTTPException: Raised with 401 Unauthorized if the token is invalid or missing the "sub" claim.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return str(user_id)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id_from_token(token: str) -> str:
    """
    Extract the user id contained in a JWT access token.
    
    Parameters:
        token (str): JWT access token string to validate and decode.
    
    Returns:
        str: The token's `sub` claim representing the user id.
    """
    return _decode_token(token)
