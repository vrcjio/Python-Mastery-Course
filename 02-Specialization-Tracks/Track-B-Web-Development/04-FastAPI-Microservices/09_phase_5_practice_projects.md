# FastAPI Phase 5 Hands-On Industry Projects

Yeh document 2 enterprise-grade security aur cryptography-focused projects provide karta hai jo strictly **Phase 5 (OAuth2 Password Bearer, Dual JWT Token Architecture, Redis Token Blacklisting, Role-Based Access Control, Argon2 Hashing, aur Fernet Symmetric Encryption)** par based hain.

---

# Project 1: Enterprise Multi-Tier RBAC Auth & Token Lifecycle Engine

### 1. Problem Statement
Ek enterprise SaaS application ke liye complete authentication aur authorization engine build karna hai:
- User signup ke waqt passwords ko memory-hard hashing (`Argon2id` ya `bcrypt`) se secure karein.
- Login standard **OAuth2 Password Bearer Flow** follow kare (`POST /api/v1/auth/login`), jo access token (15 mins) aur refresh token (7 days) provide kare.
- **Token Revocation (Logout)**: User logout kare toh uske token ka unique identifier (`jti`) Redis blacklist table me store ho taaki stolen token reuse na ho sake.
- **Role-Based Access Control (RBAC)**: Endpoints tier-wise protected hon (`SuperAdmin`, `TenantAdmin`, `Staff`, `Auditor`).

### 2. Architecture & File Structure

```
auth_engine/
│
├── core/
│   ├── config.py           # JWT secrets, algorithms, token lifetimes
│   ├── hashing.py          # Passlib CryptContext (Argon2 / Bcrypt)
│   ├── token_manager.py    # JWT encode/decode & JTI validation
│   └── dependencies.py     # OAuth2Bearer & RequireRole dependencies
│
├── schemas/
│   └── auth_schema.py      # Registration, Login response & Token payloads
│
├── routers/
│   ├── auth_router.py      # Login, Refresh, Logout endpoints
│   └── protected_router.py # RBAC demo endpoints
│
└── main.py                 # ASGI configuration
```

### 3. Implementation Code

```python
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
import jwt

# ----------------------------------------------------
# 1. Core Configuration & Hashing Setup
# ----------------------------------------------------
JWT_SECRET = "production-secure-32-byte-secret-key-phase5"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7

# Memory-hard hashing context
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Mock Stores (Production me PostgreSQL & Redis use honge)
USER_DATABASE: dict[str, dict] = {}
REVOKED_TOKENS_BLACKLIST: set[str] = set()

# ----------------------------------------------------
# 2. Schemas
# ----------------------------------------------------
UserRole = Literal["SUPERADMIN", "TENANT_ADMIN", "STAFF"]

class UserRegisterDTO(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    role: UserRole = "STAFF"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserContext(BaseModel):
    user_id: str
    email: EmailStr
    role: UserRole
    jti: str

# ----------------------------------------------------
# 3. Security Helpers
# ----------------------------------------------------
def hash_secret(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_secret(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_jwt(subject: str, role: str, token_type: Literal["access", "refresh"]) -> str:
    now = datetime.now(timezone.utc)
    delta = timedelta(minutes=ACCESS_TOKEN_MINUTES) if token_type == "access" else timedelta(days=REFRESH_TOKEN_DAYS)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + delta,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def parse_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("jti") in REVOKED_TOKENS_BLACKLIST:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

# ----------------------------------------------------
# 4. Dependency Injection Guards
# ----------------------------------------------------
async def get_authenticated_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserContext:
    payload = parse_jwt(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token required.")
    
    return UserContext(
        user_id=payload["sub"],
        email=payload["sub"],
        role=payload["role"],
        jti=payload["jti"]
    )

class EnforceRoles:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[UserContext, Depends(get_authenticated_user)]) -> UserContext:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied! Required: {self.allowed_roles}, Your role: '{user.role}'"
            )
        return user

# ----------------------------------------------------
# 5. Application & Endpoints
# ----------------------------------------------------
app = FastAPI(title="RBAC Auth & Dual-Token Engine", version="1.0.0")

@app.post("/api/v1/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: UserRegisterDTO):
    if payload.email in USER_DATABASE:
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    USER_DATABASE[payload.email] = {
        "email": payload.email,
        "full_name": payload.full_name,
        "password_hash": hash_secret(payload.password),
        "role": payload.role
    }
    return {"message": "User registered successfully", "email": payload.email, "role": payload.role}

@app.post("/api/v1/auth/token", response_model=TokenResponse)
async def login_for_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = USER_DATABASE.get(form_data.username)
    if not user or not verify_secret(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access = generate_jwt(subject=user["email"], role=user["role"], token_type="access")
    refresh = generate_jwt(subject=user["email"], role=user["role"], token_type="refresh")

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=ACCESS_TOKEN_MINUTES * 60
    )

@app.post("/api/v1/auth/logout")
async def logout(current_user: Annotated[UserContext, Depends(get_authenticated_user)]):
    # Blacklist current token's JTI
    REVOKED_TOKENS_BLACKLIST.add(current_user.jti)
    return {"status": "SUCCESS", "message": "Token revoked. Logged out safely."}

@app.get("/api/v1/workspaces/staff")
async def staff_portal(user: Annotated[UserContext, Depends(EnforceRoles(["STAFF", "TENANT_ADMIN", "SUPERADMIN"]))]):
    return {"status": "Authorized", "message": f"Welcome Staff member: {user.email}"}

@app.get("/api/v1/workspaces/admin-only")
async def superadmin_portal(user: Annotated[UserContext, Depends(EnforceRoles(["SUPERADMIN"]))]):
    return {"status": "Authorized", "message": f"Welcome SuperAdmin: {user.email}"}
```

---

# Project 2: Confidential Financial Document Vault with At-Rest Field Encryption

### 1. Problem Statement
Ek financial compliance microservice build karni hai jisme users confidential documents aur identity numbers (Aadhaar, SSN, Bank Account Numbers, SWIFT codes) upload karte hain:
- Plaintext sensitive identifiers database me **kabhi nahi** store hone chahiye.
- Application layer par **Fernet Symmetric Cryptography (AES-128-CBC with HMAC-SHA256)** implement karein.
- Master cryptographic encryption key environment variable se derive ho via PBKDF2HMAC.
- Data fetch karte waqt authorized users ke liye transparent decryption support ho.
- Har sensitive record ke decryption access par compliance audit trail generate ho.

### 2. Architecture & Patterns Covered
- **Symmetric Encryption Engine**: Fernet wrapper class jo automated base64 encode/decode aur decryption exceptions handle kare.
- **Masking Strategy**: Response schemas me decrypted details masking ke sath show hon (e.g. `XXXX-XXXX-1234`).
- **Audit Interceptor**: Decorator / dependency jo capture kare kis admin ne kab sensitive data decrypt kiya.

### 3. Implementation Code

```python
import base64
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

app = FastAPI(title="Encrypted Financial Document Vault", version="1.0.0")

# ----------------------------------------------------
# 1. Cryptographic Key Derivation Engine (PBKDF2)
# ----------------------------------------------------
MASTER_PASSPHRASE = "production-enterprise-finance-vault-secret"
CRYPTO_SALT = b"finance_secure_app_salt_16"

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=CRYPTO_SALT,
    iterations=150_000,
)
encryption_key = base64.urlsafe_b64encode(kdf.derive(MASTER_PASSPHRASE.encode()))
cipher = Fernet(encryption_key)

def encrypt_sensitive_string(raw_text: str) -> str:
    """Returns encrypted base64 string."""
    return cipher.encrypt(raw_text.encode("utf-8")).decode("utf-8")

def decrypt_sensitive_string(cipher_text: str) -> str:
    """Decrypts base64 ciphertext back to plain string."""
    try:
        return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cryptographic decryption failed. Data corruption or wrong key."
        )

# ----------------------------------------------------
# 2. In-Memory Vault & Audit Logs
# ----------------------------------------------------
ENCRYPTED_VAULT_DB: dict[UUID, dict] = {}
COMPLIANCE_AUDIT_LOGS: list[dict] = []

# ----------------------------------------------------
# 3. Schemas
# ----------------------------------------------------
DocType = Literal["TAX_IDENTIFIER", "BANK_ACCOUNT", "PASSPORT"]

class DocumentDepositRequest(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=100)
    document_type: DocType
    raw_sensitive_number: str = Field(..., min_length=6, max_length=40, description="e.g. Bank Account or Tax ID")

class DocumentSummaryResponse(BaseModel):
    document_id: UUID
    client_name: str
    document_type: DocType
    encrypted_payload_sample: str
    masked_preview: str

class DecryptedDocumentAuditResponse(BaseModel):
    document_id: UUID
    client_name: str
    document_type: DocType
    plain_sensitive_number: str
    accessed_by: str
    decrypted_at: datetime

# ----------------------------------------------------
# 4. Dependency Injection for Security Clearance
# ----------------------------------------------------
def verify_auditor_credentials(
    x_auditor_token: Annotated[str | None, Header(description="High-security Auditor Key")] = None
) -> str:
    if not x_auditor_token or x_auditor_token != "AUDITOR-CLEARANCE-PASS-99":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Clearance Denied! Requires Auditor authorization."
        )
    return "Auditor_Agent_01"

# ----------------------------------------------------
# 5. Endpoints
# ----------------------------------------------------
@app.post("/api/v1/vault/documents", response_model=DocumentSummaryResponse, status_code=status.HTTP_201_CREATED)
async def deposit_document(payload: DocumentDepositRequest):
    doc_id = uuid4()
    
    # Encrypt sensitive identifier at application layer
    ciphertext = encrypt_sensitive_string(payload.raw_sensitive_number)
    
    # Create masked preview (e.g., *******1234)
    last_four = payload.raw_sensitive_number[-4:] if len(payload.raw_sensitive_number) >= 4 else "XXXX"
    masked_val = f"{'*' * (len(payload.raw_sensitive_number) - len(last_four))}{last_four}"

    ENCRYPTED_VAULT_DB[doc_id] = {
        "id": doc_id,
        "client_name": payload.client_name,
        "document_type": payload.document_type,
        "encrypted_data": ciphertext,
        "masked_preview": masked_val,
        "created_at": datetime.now(timezone.utc)
    }

    return DocumentSummaryResponse(
        document_id=doc_id,
        client_name=payload.client_name,
        document_type=payload.document_type,
        encrypted_payload_sample=ciphertext[:24] + "...",
        masked_preview=masked_val
    )

@app.get("/api/v1/vault/documents/{document_id}/decrypt", response_model=DecryptedDocumentAuditResponse)
async def retrieve_decrypted_document(
    document_id: UUID,
    auditor: Annotated[str, Depends(verify_auditor_credentials)]
):
    record = ENCRYPTED_VAULT_DB.get(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found in vault.")

    # Transparent Decryption
    decrypted_plain = decrypt_sensitive_string(record["encrypted_data"])

    # Compliance Audit Trail
    audit_entry = {
        "document_id": str(document_id),
        "accessed_by": auditor,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    COMPLIANCE_AUDIT_LOGS.append(audit_entry)

    return DecryptedDocumentAuditResponse(
        document_id=document_id,
        client_name=record["client_name"],
        document_type=record["document_type"],
        plain_sensitive_number=decrypted_plain,
        accessed_by=auditor,
        decrypted_at=datetime.now(timezone.utc)
    )

@app.get("/api/v1/vault/compliance/audit-logs")
async def get_audit_trail(auditor: Annotated[str, Depends(verify_auditor_credentials)]):
    return {"total_audits": len(COMPLIANCE_AUDIT_LOGS), "logs": COMPLIANCE_AUDIT_LOGS}
```

---

## 4. How to Run & Verify Phase 5 Projects

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn[standard] pyjwt passlib[argon2,bcrypt] cryptography python-multipart
```

### Step 2: Verification Checklist for Project 1 (RBAC & Auth)
1. Run application:
   ```bash
   uvicorn project1:app --reload --port 8000
   ```
2. Open Swagger UI at `http://127.0.0.1:8000/docs`.
3. Call `POST /api/v1/auth/signup` to register a `STAFF` account and a `SUPERADMIN` account.
4. Click the green **Authorize** padlock button at the top right of Swagger, enter the credentials, and receive the Bearer access token.
5. Try accessing `/api/v1/workspaces/admin-only` using the `STAFF` token. Expected: `403 Forbidden`.
6. Call `POST /api/v1/auth/logout`. Try accessing any protected endpoint with that token. Expected: `401 Unauthorized (Token has been revoked)`.

### Step 3: Verification Checklist for Project 2 (Fernet Encryption)
1. Deposit a record:
   - Call `POST /api/v1/vault/documents` with raw data `"987654321098"`.
   - Inspect the response: check that the raw data is nowhere to be found, and only an encrypted blob and masked string `********1098` are returned.
2. Attempt decryption:
   - Call `GET /api/v1/vault/documents/{id}/decrypt` without headers. Expected: `403 Forbidden`.
   - Supply header `X-Auditor-Token: AUDITOR-CLEARANCE-PASS-99`. Expected: `200 OK` with full plaintext number and an entry added to `/api/v1/vault/compliance/audit-logs`.