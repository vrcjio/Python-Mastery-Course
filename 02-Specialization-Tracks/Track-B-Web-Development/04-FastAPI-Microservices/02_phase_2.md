# FastAPI Phase 2 Developer Handbook: Data Validation & Serialization (Pydantic V2)

Yeh handbook FastAPI aur **Pydantic V2** ke deep integration, specialized enterprise data types, complex schema modeling, custom validators, aur multipart file handling ka production-level reference guide hai.

---

## 1. Pydantic V2 Core Architecture & Performance

Pydantic V2 ka core engine C/Rust (`pydantic-core`) par rewritten hai, jo V1 ke mukable 5x se 20x fast parsing aur validation provide karta hai.

### 1.1 V1 vs V2 Breaking Changes Checklist

| Feature | Pydantic V1 (Legacy) | Pydantic V2 (Modern Standard) |
| :--- | :--- | :--- |
| Single Field Validator | `@validator('field')` | `@field_validator('field')` |
| Whole Model Validator | `@root_validator` | `@model_validator(mode='before' / 'after')` |
| Export Dict | `model.dict()` | `model.model_dump()` |
| Export JSON | `model.json()` | `model.model_dump_json()` |
| Config Definition | `class Config:` inner class | `model_config = ConfigDict(...)` |
| Computed Property | `@property` (not serialized) | `@computed_field` (auto-serialized) |

---

## 2. Specialized & Enterprise Data Types

FastAPI me standard types (`int`, `str`, `float`, `bool`) ke alawa complex data types ke built-in validation aur serialization rules hote hain:

```python
from decimal import Decimal
from datetime import datetime, date, timezone
from uuid import UUID, uuid4
from ipaddress import IPv4Address
from enum import StrEnum
from pydantic import BaseModel, Field, EmailStr, HttpUrl, SecretStr

class AccountTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class EnterpriseProfile(BaseModel):
    # Unique identifier
    user_id: UUID = Field(default_factory=uuid4)
    
    # Financial precision (never use float for currency)
    wallet_balance: Decimal = Field(..., max_digits=12, decimal_places=4, ge=Decimal("0.0000"))
    
    # Contact & Identity
    official_email: EmailStr
    website: HttpUrl
    client_ip: IPv4Address
    
    # Secure field (string masking in logs / print)
    api_secret_key: SecretStr
    
    # Enums & Dates
    tier: AccountTier = AccountTier.FREE
    date_of_birth: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

> **Security Note:** `SecretStr` sensitive tokens ya passwords ko accidental logging aur string prints se prevent karta hai (`str(secret)` masked value dega, real string ke liye `secret.get_secret_value()` use karein).

---

## 3. Pydantic V2 Validators

Pydantic V2 me validation do primary layers par hoti hai: Single Field level aur Whole Model (cross-field) level.

### 3.1 `@field_validator`

Used for individual field validation, string cleanup, parsing, and sanitation:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class UserRegistration(BaseModel):
    username: str
    referral_code: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, raw_value: str) -> str:
        if not isinstance(raw_value, str):
            raise ValueError("Username must be a valid string")
        cleaned = raw_value.strip().lower()
        if len(cleaned) < 3:
            raise ValueError("Username must contain at least 3 characters")
        return cleaned

    @field_validator("referral_code")
    @classmethod
    def validate_referral_format(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        if not value.startswith("REF-"):
            raise ValueError("Referral code must begin with prefix 'REF-'")
        return value.upper()
```

### 3.2 `@model_validator`

Used jab ek field ki validity doosre field par depend kare (e.g., password matching, conditional dates):

```python
from pydantic import BaseModel, model_validator

class PasswordResetRequest(BaseModel):
    new_password: str
    confirm_password: str
    two_factor_code: str | None = None
    is_sms_auth: bool = False

    @model_validator(mode="after")
    def verify_credentials_integrity(self) -> "PasswordResetRequest":
        # Check 1: Cross-field match
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        
        # Check 2: Conditional requirement
        if self.is_sms_auth and not self.two_factor_code:
            raise ValueError("two_factor_code is strictly required when is_sms_auth is True")
            
        return self
```

---

## 4. Computed Fields & Custom Serialization

### 4.1 `@computed_field`

Dynamic attributes calculate karke directly API response JSON me deliver karta hai:

```python
from decimal import Decimal
from pydantic import BaseModel, computed_field

class InvoiceItem(BaseModel):
    item_id: str
    quantity: int
    unit_price: Decimal

    @computed_field
    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price

    @computed_field
    @property
    def tax_estimate(self) -> Decimal:
        return (self.total_price * Decimal("0.18")).quantize(Decimal("0.01"))
```

### 4.2 `model_dump` & `model_dump_json` Filtering

Production me internal DB fields ya raw credentials ko serialize hone se rokne ke techniques:

```python
invoice = InvoiceItem(item_id="SKU-99", quantity=4, unit_price=Decimal("150.00"))

# Dict export with field exclusions
safe_dict = invoice.model_dump(
    exclude={"unit_price"}, 
    mode="python"
)

# JSON export with explicit formatting
json_output = invoice.model_dump_json(
    indent=2,
    by_alias=True
)
```

---

## 5. Nested Models & Self-Referencing (Recursive) Schemas

### 5.1 Nested Hierarchies

```python
from pydantic import BaseModel, Field

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class Address(BaseModel):
    street: str
    city: str
    pincode: str
    geo: GeoLocation

class Merchant(BaseModel):
    id: int
    company_name: str
    headquarters: Address
    branches: list[Address] = []
```

### 5.2 Self-Referencing Recursive Models

Tree structures, comment threads, ya organizational hierarchy store karne ke liye:

```python
from typing import Self
from pydantic import BaseModel

class CommentNode(BaseModel):
    id: int
    author: str
    text: str
    replies: list[Self] = []  # References itself dynamically in Python 3.11+
```

---

## 6. Form Fields & File Handling (`UploadFile`)

FastAPI me JSON data ke sath multipart files handle karne ke patterns:

### 6.1 Form Data vs JSON Body

* JSON body (`Content-Type: application/json`): Default for API requests.
* Form data (`Content-Type: multipart/form-data`): Required for file uploads aur legacy HTML forms.

### 6.2 Safe File Uploads with Streaming (RAM Protection)

Agar user 500MB ki file upload kare, toh `await file.read()` puri file RAM me load kar dega, jisse server crash ho sakta hai. Chunk-based streaming safe pattern hai:

```python
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status

app = FastAPI()

UPLOAD_DIR = Path("./uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "application/pdf"}

@app.post("/upload/document", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_title: str = Form(..., min_length=3, max_length=100),
    file: UploadFile = File(...)
):
    # 1. Content-Type Validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Allowed: {ALLOWED_MIME_TYPES}"
        )

    destination_file = UPLOAD_DIR / file.filename
    bytes_written = 0

    # 2. Chunk-based disk streaming (Max 1MB chunk in memory at a time)
    try:
        with destination_file.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunk
                bytes_written += len(chunk)
                if bytes_written > MAX_FILE_SIZE_BYTES:
                    # Cleanup partially uploaded file
                    destination_file.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeded maximum limit of 50MB"
                    )
                buffer.write(chunk)
    finally:
        await file.close()

    return {
        "status": "success",
        "title": document_title,
        "filename": file.filename,
        "bytes_stored": bytes_written
    }
```

---

## 7. Phase 2 Complete Integrated Demo Endpoint

Yeh sample pattern showcase karta hai complex data types, validation, nested schemas, aur computed serialization ka combined use:

```python
from fastapi import FastAPI, status
from pydantic import BaseModel, Field, EmailStr, computed_field
from decimal import Decimal
from uuid import UUID, uuid4

app = FastAPI(title="Phase 2 Integrated API")

# Schemas
class OrderItemSchema(BaseModel):
    sku: str = Field(..., pattern=r"^[A-Z]{3}-\d{4}$")
    unit_price: Decimal = Field(..., gt=Decimal("0.0"))
    quantity: int = Field(..., ge=1, le=100)

class OrderCreateRequest(BaseModel):
    customer_email: EmailStr
    items: list[OrderItemSchema] = Field(..., min_length=1)

class OrderResponse(BaseModel):
    order_id: UUID = Field(default_factory=uuid4)
    customer_email: EmailStr
    items: list[OrderItemSchema]
    
    @computed_field
    @property
    def grand_total(self) -> Decimal:
        return sum(item.unit_price * item.quantity for item in self.items)

# Endpoint
@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Validated Order"
)
async def create_order(payload: OrderCreateRequest):
    return OrderResponse(
        customer_email=payload.customer_email,
        items=payload.items
    )
```

---

## 8. Phase 2 Mastery Checklist

- [ ] Pydantic V2 syntax (`@field_validator`, `@model_validator`, `model_config`) thoroughly clear hai?
- [ ] Financial data ke liye `Decimal` aur security ke liye `SecretStr` implement kiya?
- [ ] Chunk-wise file streaming ka practical logic samajh gaya taaki server OOM (Out Of Memory) crash na ho?
- [ ] Nested models aur dynamic `@computed_field` ka serialization pipeline clear hai?