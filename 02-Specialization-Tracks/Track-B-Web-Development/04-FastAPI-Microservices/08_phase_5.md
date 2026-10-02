# FastAPI Phase 5 Developer Handbook: Security, Cryptography & Authentication

Yeh handbook FastAPI me production-grade security architecture ka complete reference guide hai. Isme modern cryptographic hashing, OAuth2 Password Bearer flow, Access/Refresh JWT lifecycle, Role-Based Access Control (RBAC), data-at-rest field encryption (AES/Fernet), aur API attack mitigation strategies shamil hain.

---

## 1. Cryptographic Password Hashing (Argon2 vs Bcrypt)

Purane algorithms jaise SHA256 ya MD5 fast hote hain aur rainbow-table/GPU attacks ke aage compromise ho jate hain. Industry standard **memory-hard** aur **CPU-hard** algorithms use karta hai.

### 1.1 Kyu Argon2id ya Modern Bcrypt?
- **Argon2id**: Password Hashing Competition (PHC) ka winner; side-channel attacks aur GPU/ASIC cracking ke khilaaf maximum resistance deta hai.
- **Bcrypt**: Proven legacy battle-tested hashing standard.

### 1.2 Cryptographic Hash Utility (`pwd_context`)

```python
# app/core/security.py
from passlib.context import CryptContext

# Argon2id prioritized, fallback to bcrypt
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB memory consumption per hash
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=4       # 4 concurrent threads
)

def hash_password(plain_password: str) -> str:
    """Hashes plain password using salt & memory-hard algorithm."""
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain input against stored hash using constant-time comparison."""
    return pwd_context.verify(plain_password, hashed_password)
```

---

## 2. JWT (JSON Web Tokens) Dual-Token Architecture

Single long-lived token leak hone par massive risk hota hai. Industry architecture **Short-Lived Access Token** + **Long-Lived Refresh Token** model follow karti hai.

```
Client               FastAPI Backend             Redis Blacklist
  │                        │                            │
  ├── 1. POST /token ─────▶│ (Verify credentials)       │
  │◀── Access (15m) + ─────┤                            │
  │    Refresh (7d) ───────┤                            │
  │                        │                            │
  ├── 2. GET /secure ─────▶│ (Verify Access Token)      │
  │                        │                            │
  ├── 3. POST /refresh ───▶│ (Check if Revoked?)───────▶│
  │◀── New Access ─────────┤                            │
  │                        │                            │
  ├── 4. POST /logout ────▶│ (Add JTI to Blacklist)────▶│ (Store JTI with TTL)
```

### 2.1 Token Utility & Lifecycle Engine

```python
# app/core/jwt_handler.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt  # PyJWT library
from fastapi import HTTPException, status
from pydantic import BaseModel

SECRET_KEY = "SUPER_SECRET_STRONG_KEY_CHANGE_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenPayload(BaseModel):
    sub: str           # User identifier (e.g. UUID / email)
    role: str          # User role (e.g. admin, user)
    jti: str           # Unique JWT ID (for revocation)
    exp: datetime
    type: str          # "access" or "refresh"

def create_token(subject: str, role: str, token_type: str = "access", expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + (timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) if token_type == "access" else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "jti": jti,
        "exp": expire,
        "iat": now,
        "type": token_type
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired. Please login or refresh token."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )
```

---

## 3. OAuth2 Bearer & Role-Based Access Control (RBAC)

FastAPI ka `OAuth2PasswordBearer` Swagger UI me "Authorize" padlock open karta hai aur automatically `Authorization: Bearer <token>` header extract karta hai.

### 3.1 Declarative RBAC Dependency Provider

```python
# app/core/dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class CurrentUserContext:
    def __init__(self, user_id: str, role: str, jti: str):
        self.user_id = user_id
        self.role = role
        self.jti = jti

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> CurrentUserContext:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required for this action."
        )
    
    # In production: Check Redis if payload["jti"] is blacklisted
    return CurrentUserContext(
        user_id=payload["sub"],
        role=payload["role"],
        jti=payload["jti"]
    )

class RequireRoles:
    """Class-based dependency factory for role checking."""
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[CurrentUserContext, Depends(get_current_user)]) -> CurrentUserContext:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {self.allowed_roles}, your role: '{user.role}'"
            )
        return user
```

---

## 4. Data-at-Rest Encryption (Fernet / AES-128-CBC with HMAC)

Passwords ko **hash** kiya jata hai (one-way), lekin sensitive data jaise Credit Card numbers, Bank Account details, Aadhaar cards, ya API Secrets ko decrypt karne ki zaroorat hoti hai. Iske liye **Symmetric Encryption** use hoti hai.

### 4.1 Field Encryption Engine

```python
# app/core/encryption.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SymmetricEncryptor:
    def __init__(self, master_passphrase: str, salt: bytes = b"static_app_salt_prod_16b"):
        # Derive cryptographic 32-byte Fernet key from passphrase
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(master_passphrase.encode()))
        self.cipher = Fernet(derived_key)

    def encrypt(self, plain_text: str) -> str:
        """Encrypts UTF-8 plain string into URL-safe base64 encrypted ciphertext."""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        """Decrypts ciphertext back to original plain string."""
        return self.cipher.decrypt(cipher_text.encode()).decode()

# Global instance for app lifecycle
crypto_engine = SymmetricEncryptor(master_passphrase="enterprise-vault-super-key")
```

---

## 5. API Hardening & Attack Mitigations

Production APIs par automated bots, brute force, clickjacking, aur cross-origin injection attacks aate hain.

### 5.1 Security Headers Middleware
Har response ke sath defense-in-depth headers inject karna:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### 5.2 CORS (Cross-Origin Resource Sharing)
Wildcard (`*`) production me allow mat karein:

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://dashboard.example.com",
    "https://admin.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)
```

### 5.3 Rate Limiting with `slowapi`
Brute-force attacks aur API abuse prevent karne ke liye:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(request: Request):
    return {"message": "Proceeding with login..."}
```

---

## 6. Complete End-to-End Security Architecture Flow

Niche diya gaya complete executable script authentication, RBAC, aur field encryption ko synthesize karta hai:

```python
# main_security_demo.py
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password
from app.core.jwt_handler import create_token, decode_token
from app.core.dependencies import get_current_user, RequireRoles, CurrentUserContext
from app.core.encryption import crypto_engine

app = FastAPI(title="Phase 5 Secure Auth & Cryptography Service")

# Mock In-Memory DB
USERS_DB = {}
VAULT_DB = {}

# Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "customer"  # "admin" or "customer"

class VaultSecretStore(BaseModel):
    document_title: str
    sensitive_data: str  # E.g. SSN or Bank Account

# 1. Registration (Hashing)
@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    if payload.email in USERS_DB:
        raise HTTPException(status_code=400, detail="User already registered.")
    
    USERS_DB[payload.email] = {
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role
    }
    return {"status": "User created successfully"}

# 2. Login (OAuth2 Password Flow + Dual Tokens)
@app.post("/api/v1/auth/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(subject=user["email"], role=user["role"], token_type="access")
    refresh_token = create_token(subject=user["email"], role=user["role"], token_type="refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# 3. Encrypted Data Ingestion (Customer or Admin)
@app.post("/api/v1/vault/store")
async def store_secret_in_vault(
    payload: VaultSecretStore,
    current_user: Annotated[CurrentUserContext, Depends(get_current_user)]
):
    encrypted_cipher = crypto_engine.encrypt(payload.sensitive_data)
    record_id = len(VAULT_DB) + 1
    
    VAULT_DB[record_id] = {
        "owner": current_user.user_id,
        "title": payload.document_title,
        "encrypted_blob": encrypted_cipher
    }
    return {"status": "Stored securely", "record_id": record_id}

# 4. Decrypted Data Retrieval (Protected by RBAC: Admin ONLY)
@app.get("/api/v1/vault/admin/inspect/{record_id}")
async def inspect_vault_secret(
    record_id: int,
    admin_user: Annotated[CurrentUserContext, Depends(RequireRoles(["admin"]))]
):
    record = VAULT_DB.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vault entry not found.")

    decrypted_content = crypto_engine.decrypt(record["encrypted_blob"])
    return {
        "record_id": record_id,
        "title": record["title"],
        "owner": record["owner"],
        "decrypted_plaintext": decrypted_content,
        "inspected_by": admin_user.user_id
    }
```

---

## 7. Phase 5 Mastery Checklist

- [ ] Plain passwords database me store nahi ho rahe aur **Argon2id/Bcrypt** standard follow ho raha hai?
- [ ] Swagger `/docs` par login karne ke liye `OAuth2PasswordBearer` configured hai?
- [ ] JWT tokens me `exp` expiration, `iat`, aur unique `jti` standard registered claims shaamil hain?
- [ ] Roles enforce karne ke liye modular dependency wrappers (`RequireRoles(["admin"])`) use ho rahe hain?
- [ ] Confidential data (tax IDs, cards, keys) DB me insert hone se pehle **Fernet symmetric encryption** se encrypt hota hai?
- [ ] Production setup me Security Headers aur strict CORS origins enabled hain?