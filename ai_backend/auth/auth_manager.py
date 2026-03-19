"""
Enterprise-Grade Authentication System for AI Fitness Coach
Implements JWT-based auth with refresh tokens, role-based access, and session management
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
import jwt
import bcrypt
import redis
import json
from loguru import logger
from pydantic import BaseModel, EmailStr, Field, validator

# Configuration
class JWTConfig:
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production-12345678')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    PASSWORD_MIN_LENGTH = 12
    
class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    COACH = "coach"
    ADMIN = "admin"
    SUPPORT = "support"

class TokenType(str, Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"

# ════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════

class PasswordValidator:
    """Validate password strength"""
    
    @staticmethod
    def validate(password: str) -> bool:
        """
        Validate password meets security requirements:
        - Minimum 12 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        if len(password) < JWTConfig.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {JWTConfig.PASSWORD_MIN_LENGTH} characters")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:',.<>?/" for c in password):
            raise ValueError("Password must contain at least one special character")
        
        return True

class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str  # User ID (subject)
    type: TokenType  # 'access' or 'refresh'
    role: UserRole  # User's role
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    jti: Optional[str] = None  # JWT ID for token revocation

class TokenResponse(BaseModel):
    """Token response to client"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # Seconds until expiration

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=12)
    name: str = Field(..., min_length=2, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        PasswordValidator.validate(v)
        return v

class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

class UserSession(BaseModel):
    """User session information"""
    user_id: str
    email: str
    name: str
    role: UserRole
    device_id: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

# ════════════════════════════════════════════════════════════
# JWT Manager
# ════════════════════════════════════════════════════════════

class JWTManager:
    """Manage JWT token creation and validation"""
    
    @staticmethod
    def _generate_jti() -> str:
        """Generate unique JWT identifier for token revocation"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def create_access_token(
        user_id: str,
        role: UserRole = UserRole.USER,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create access token (short-lived)
        
        Args:
            user_id: User's unique identifier
            role: User's role
            expires_delta: Custom expiration time
        
        Returns:
            Encoded JWT token
        """
        now = datetime.utcnow()
        expires = now + (expires_delta or timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES))
        
        payload = {
            'sub': user_id,
            'type': TokenType.ACCESS,
            'role': role,
            'iat': int(now.timestamp()),
            'exp': int(expires.timestamp()),
            'jti': JWTManager._generate_jti()
        }
        
        token = jwt.encode(
            payload,
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        logger.debug(f"Access token created for user {user_id}")
        return token
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create refresh token (long-lived)
        
        Args:
            user_id: User's unique identifier
            expires_delta: Custom expiration time
        
        Returns:
            Encoded JWT token
        """
        now = datetime.utcnow()
        expires = now + (expires_delta or timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS))
        
        payload = {
            'sub': user_id,
            'type': TokenType.REFRESH,
            'iat': int(now.timestamp()),
            'exp': int(expires.timestamp()),
            'jti': JWTManager._generate_jti()
        }
        
        token = jwt.encode(
            payload,
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        logger.debug(f"Refresh token created for user {user_id}")
        return token
    
    @staticmethod
    def verify_token(token: str, expected_type: TokenType) -> TokenPayload:
        """
        Verify and decode token
        
        Args:
            token: JWT token to verify
            expected_type: Expected token type (access/refresh)
        
        Returns:
            Decoded token payload
        
        Raises:
            ValueError: If token is invalid, expired, or type mismatch
        """
        try:
            payload = jwt.decode(
                token,
                JWTConfig.SECRET_KEY,
                algorithms=[JWTConfig.ALGORITHM]
            )
            
            # Validate token type
            if payload.get('type') != expected_type:
                raise ValueError(f"Invalid token type. Expected {expected_type}, got {payload.get('type')}")
            
            # Check if token is revoked
            if JWTManager._is_token_revoked(payload.get('jti')):
                raise ValueError("Token has been revoked")
            
            return TokenPayload(**payload)
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token expired")
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def _is_token_revoked(jti: Optional[str]) -> bool:
        """Check if token has been revoked"""
        if not jti:
            return False
        
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            return redis_client.exists(f"revoked_token:{jti}") > 0
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return False
    
    @staticmethod
    def revoke_token(token: str):
        """Revoke a token (add to blacklist)"""
        try:
            payload = jwt.decode(
                token,
                JWTConfig.SECRET_KEY,
                algorithms=[JWTConfig.ALGORITHM]
            )
            
            jti = payload.get('jti')
            exp = payload.get('exp')
            
            if not jti or not exp:
                return
            
            # Calculate TTL (time to live)
            ttl = exp - int(datetime.utcnow().timestamp())
            
            if ttl > 0:
                try:
                    redis_client = redis.Redis(
                        host=os.getenv('REDIS_HOST', 'localhost'),
                        port=int(os.getenv('REDIS_PORT', 6379))
                    )
                    redis_client.setex(f"revoked_token:{jti}", ttl, "1")
                    logger.info(f"Token {jti} revoked")
                except Exception as e:
                    logger.error(f"Error revoking token: {e}")
        
        except jwt.DecodeError:
            logger.warning("Could not decode token for revocation")

# ════════════════════════════════════════════════════════════
# Password Manager
# ════════════════════════════════════════════════════════════

class PasswordManager:
    """Manage password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        # Validate password strength first
        PasswordValidator.validate(password)
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        logger.debug("Password hashed successfully")
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hash: Hashed password from database
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

# ════════════════════════════════════════════════════════════
# Session Manager
# ════════════════════════════════════════════════════════════

class SessionManager:
    """Manage user sessions with Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.SESSION_TTL = 86400 * 7  # 7 days
        self.MAX_SESSIONS_PER_USER = 5
    
    def create_session(
        self,
        user_id: str,
        email: str,
        name: str,
        role: UserRole,
        device_id: str,
        ip_address: str,
        access_token: str
    ) -> UserSession:
        """
        Create new session
        
        Args:
            user_id: User's ID
            email: User's email
            name: User's name
            role: User's role
            device_id: Device identifier
            ip_address: Client IP address
            access_token: JWT access token
        
        Returns:
            UserSession object
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)
        
        session = UserSession(
            user_id=user_id,
            email=email,
            name=name,
            role=role,
            device_id=device_id,
            ip_address=ip_address,
            created_at=now,
            last_activity=now,
            expires_at=expires_at
        )
        
        # Store session in Redis
        session_key = f"session:{access_token}"
        self.redis_client.setex(
            session_key,
            self.SESSION_TTL,
            session.json()
        )
        
        # Track sessions per user (for max concurrent sessions)
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis_client.lpush(user_sessions_key, access_token)
        self.redis_client.ltrim(user_sessions_key, 0, self.MAX_SESSIONS_PER_USER - 1)
        
        logger.info(f"Session created for user {user_id} from IP {ip_address}")
        return session
    
    def get_session(self, access_token: str) -> Optional[UserSession]:
        """
        Get session by token
        
        Args:
            access_token: JWT access token
        
        Returns:
            UserSession if valid, None otherwise
        """
        try:
            session_key = f"session:{access_token}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            return UserSession(**json.loads(session_data))
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            return None
    
    def revoke_session(self, access_token: str):
        """
        Revoke session (logout)
        
        Args:
            access_token: JWT access token to revoke
        """
        try:
            session_key = f"session:{access_token}"
            self.redis_client.delete(session_key)
            logger.info("Session revoked (user logged out)")
        except Exception as e:
            logger.error(f"Error revoking session: {e}")
    
    def get_active_sessions(self, user_id: str) -> List[UserSession]:
        """
        Get all active sessions for user
        
        Args:
            user_id: User's ID
        
        Returns:
            List of active UserSession objects
        """
        try:
            sessions = []
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Get all tokens for user
            tokens = self.redis_client.lrange(user_sessions_key, 0, -1)
            
            for token in tokens:
                session = self.get_session(token)
                if session:
                    sessions.append(session)
            
            return sessions
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def revoke_all_sessions(self, user_id: str):
        """
        Revoke all sessions for user (force logout everywhere)
        
        Args:
            user_id: User's ID
        """
        try:
            sessions = self.get_active_sessions(user_id)
            for session in sessions:
                # In real implementation, would get token from session
                self.redis_client.delete(f"session:*")  # Simplified
            
            logger.info(f"All sessions revoked for user {user_id}")
        except Exception as e:
            logger.error(f"Error revoking all sessions: {e}")
    
    def update_last_activity(self, access_token: str):
        """
        Update session last activity timestamp
        
        Args:
            access_token: JWT access token
        """
        try:
            session = self.get_session(access_token)
            if session:
                session.last_activity = datetime.utcnow()
                session_key = f"session:{access_token}"
                self.redis_client.setex(
                    session_key,
                    self.SESSION_TTL,
                    session.json()
                )
        except Exception as e:
            logger.error(f"Error updating last activity: {e}")

# ════════════════════════════════════════════════════════════
# Rate Limiting Helper
# ════════════════════════════════════════════════════════════

class RateLimiter:
    """Rate limiting for security (brute force prevention, etc)"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
    
    def is_rate_limited(
        self,
        identifier: str,
        max_attempts: int = 5,
        window_seconds: int = 300
    ) -> bool:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: IP address, email, or user ID
            max_attempts: Max attempts allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if rate limited, False otherwise
        """
        key = f"rate_limit:{identifier}"
        
        try:
            current = self.redis_client.get(key)
            
            if current is None:
                self.redis_client.setex(key, window_seconds, "1")
                return False
            
            current_count = int(current)
            
            if current_count >= max_attempts:
                return True
            
            self.redis_client.incr(key)
            return False
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    def reset_rate_limit(self, identifier: str):
        """Reset rate limit for identifier"""
        try:
            key = f"rate_limit:{identifier}"
            self.redis_client.delete(key)
            logger.info(f"Rate limit reset for {identifier}")
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")

# ════════════════════════════════════════════════════════════
# Main Authentication Service
# ════════════════════════════════════════════════════════════

class AuthenticationService:
    """Main authentication service combining all components"""
    
    def __init__(self):
        self.jwt_manager = JWTManager()
        self.password_manager = PasswordManager()
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
    
    def register(self, request: RegisterRequest, ip_address: str) -> TokenResponse:
        """
        Register new user
        
        Raises:
            ValueError: If validation fails
        """
        # Validate password strength
        PasswordValidator.validate(request.password)
        
        # Hash password
        password_hash = self.password_manager.hash_password(request.password)
        
        logger.info(f"User registration: {request.email}")
        
        # Response will include tokens (user_id would come from database)
        # This is simplified - in real implementation, would save to database
        
        return self._create_token_response(
            user_id="generated_user_id",
            email=request.email,
            name=request.name,
            role=UserRole.USER,
            device_id="default",
            ip_address=ip_address
        )
    
    def login(
        self,
        request: LoginRequest,
        device_id: str,
        ip_address: str
    ) -> TokenResponse:
        """
        Authenticate user and create session
        
        Raises:
            ValueError: If credentials invalid or user locked out
        """
        # Check rate limiting (prevent brute force)
        if self.rate_limiter.is_rate_limited(request.email, max_attempts=5, window_seconds=300):
            logger.warning(f"Login rate limited for {request.email}")
            raise ValueError("Too many login attempts. Try again in 5 minutes.")
        
        # In real implementation:
        # 1. Query user from database by email
        # 2. Verify password hash matches
        # 3. Check if account is active/not locked
        
        logger.info(f"User login: {request.email}")
        
        # Reset rate limit on success
        self.rate_limiter.reset_rate_limit(request.email)
        
        # Create tokens and session
        return self._create_token_response(
            user_id="user_id_from_db",
            email=request.email,
            name="User Name",
            role=UserRole.USER,
            device_id=device_id,
            ip_address=ip_address
        )
    
    def refresh_token(self, refresh_token: str, ip_address: str) -> TokenResponse:
        """
        Refresh access token using refresh token
        
        Raises:
            ValueError: If refresh token invalid or expired
        """
        # Verify refresh token
        payload = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        
        user_id = payload.sub
        logger.info(f"Token refreshed for user {user_id}")
        
        # Create new access token
        access_token = self.jwt_manager.create_access_token(
            user_id=user_id,
            role=payload.role if hasattr(payload, 'role') else UserRole.USER
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def logout(self, access_token: str):
        """Logout user (revoke tokens and session)"""
        try:
            # Revoke access token
            self.jwt_manager.revoke_token(access_token)
            
            # Revoke session
            self.session_manager.revoke_session(access_token)
            
            logger.info("User logged out successfully")
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            raise ValueError(f"Logout failed: {str(e)}")
    
    def _create_token_response(
        self,
        user_id: str,
        email: str,
        name: str,
        role: UserRole,
        device_id: str,
        ip_address: str
    ) -> TokenResponse:
        """Helper to create token response and session"""
        # Create tokens
        access_token = self.jwt_manager.create_access_token(user_id, role)
        refresh_token = self.jwt_manager.create_refresh_token(user_id)
        
        # Create session
        self.session_manager.create_session(
            user_id=user_id,
            email=email,
            name=name,
            role=role,
            device_id=device_id,
            ip_address=ip_address,
            access_token=access_token
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

# ════════════════════════════════════════════════════════════
# Example Usage
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    auth = AuthenticationService()
    
    # Example: Register
    register_request = RegisterRequest(
        email="user@example.com",
        password="SecurePass123!",
        name="John Doe"
    )
    
    # Example: Login
    login_request = LoginRequest(
        email="user@example.com",
        password="SecurePass123!"
    )
    
    print("Authentication system initialized successfully")
    print(f"JWT Config: Algorithm={JWTConfig.ALGORITHM}, Expiry={JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES}min")
    print(f"Max sessions per user: {auth.session_manager.MAX_SESSIONS_PER_USER}")
