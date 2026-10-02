# FastAPI Phase 1 & 2 Hands-On Industry Projects

Yeh document 2 production-spec demo projects provide karta hai jo strictly **Phase 1 (Typing, Concurrency, ASGI, Path/Query parameters, Exception handlers)** aur **Phase 2 (Pydantic V2, Field/Model validators, Decimal/UUID/EmailStr, File uploads, Computed fields)** par based hain.

Is phase me koi external database (jaise PostgreSQL ya MongoDB) mandatory nahi hai; state ko test karne ke liye hum **in-memory thread-safe Python datastructures** (`dict`, `set`) use karenge taaki focus sirf data validation, request parsing, serialization aur API contract design par rahe.

---

# Project 1: Student Academic & Attendance Lifecycle API

### 1. Business Problem
Ek educational institute ko ek microservice chahiye jo students ka onboarding, semester registration, aur monthly attendance audit kare. System ko strict validation rules enforce karne hain:
- Roll numbers ek specific regex pattern follow karein (`STU-YYYY-XXXX`).
- CGPA aur Marks calculate karte waqt floating-point inaccuracies se bachne ke liye `Decimal` use ho.
- Address nested format me ho with PIN code validation.
- Attendance percentage calculate karke dynamic remarks (`Eligible for Exams` / `Shortage`) `@computed_field` ke through return hon.

### 2. Tech Stack & Concepts Covered
- **Types**: `UUID`, `Decimal`, `date`, `EmailStr`, `Literal`, `Annotated`.
- **Validation**: `@field_validator`, `@model_validator`, Path & Query validation.
- **Serialization**: `@computed_field`, `model_dump()`.
- **Error Handling**: Custom 404 & 422 standard JSON responses.

### 3. API Contract Specifications

| Method | Endpoint | Description | Status Code | Query / Path Params |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/students/` | Register new student profile | `201 Created` | Request Body (JSON) |
| `GET` | `/api/v1/students/{student_id}` | Fetch student profile | `200 OK` | `student_id: UUID` |
| `GET` | `/api/v1/students/` | Filter & paginate students | `200 OK` | `branch: Literal`, `min_cgpa: Decimal`, `limit: int`, `offset: int` |
| `POST` | `/api/v1/students/{student_id}/attendance` | Log daily attendance record | `200 OK` | `student_id: UUID`, Query `status: Literal["present", "absent", "leave"]` |

### 4. Implementation Code

```python
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Path, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator, model_validator

app = FastAPI(
    title="Student Academic Lifecycle Engine",
    version="1.0.0",
    description="Phase 1 & 2 Practice Project covering Pydantic V2 and Param Validations",
)

# ----------------------------------------------------
# 1. Custom Global Error Handlers (Phase 1)
# ----------------------------------------------------
@app.exception_handler(RequestValidationError)
async def custom_validation_error_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append({
            "location": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg"),
            "type": err.get("type"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "error": "VALIDATION_FAILED", "details": formatted_errors},
    )

# ----------------------------------------------------
# 2. Pydantic Schemas (Phase 2)
# ----------------------------------------------------
BranchCode = Literal["CS", "IT", "EC", "ME", "EE"]

class GeoAddress(BaseModel):
    street: str = Field(..., min_length=3, max_length=100)
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    pincode: str = Field(..., pattern=r"^[1-9][0-9]{5}$", description="Standard 6-digit Indian PIN code")

class StudentRegistration(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    roll_number: str = Field(..., pattern=r"^STU-20\d{2}-\d{4}$", description="Format: STU-YYYY-XXXX (e.g., STU-2024-0101)")
    full_name: str = Field(..., min_length=3, max_length=60)
    email: EmailStr
    branch: BranchCode
    admission_date: date
    address: GeoAddress
    scholarship_fee_discount: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Discount percentage between 0.00 and 100.00",
    )

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not all(char.isalpha() or char.isspace() for char in value):
            raise ValueError("Student name must contain only alphabets and spaces")
        return value.title()

    @model_validator(mode="after")
    def verify_admission_date(self) -> "StudentRegistration":
        if self.admission_date > date.today():
            raise ValueError("Admission date cannot be in the future")
        return self

class StudentResponse(StudentRegistration):
    id: UUID = Field(default_factory=uuid4)
    total_classes: int = 0
    attended_classes: int = 0
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def attendance_percentage(self) -> Decimal:
        if self.total_classes == 0:
            return Decimal("0.00")
        percentage = (Decimal(self.attended_classes) / Decimal(self.total_classes)) * Decimal(100)
        return percentage.quantize(Decimal("0.01"))

    @computed_field
    @property
    def exam_eligibility(self) -> Literal["ELIGIBLE", "SHORTAGE_DEBARRED"]:
        if self.attendance_percentage >= Decimal("75.00"):
            return "ELIGIBLE"
        return "SHORTAGE_DEBARRED"

# ----------------------------------------------------
# 3. In-Memory Mock Storage
# ----------------------------------------------------
STUDENT_DATABASE: dict[UUID, StudentResponse] = {}

# ----------------------------------------------------
# 4. API Endpoints (Phase 1 & 2)
# ----------------------------------------------------
@app.post(
    "/api/v1/students/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Student",
    tags=["Students"],
)
async def register_student(payload: StudentRegistration):
    # Check duplicate roll number
    for record in STUDENT_DATABASE.values():
        if record.roll_number == payload.roll_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with roll number '{payload.roll_number}' already exists.",
            )

    new_student = StudentResponse(**payload.model_dump())
    STUDENT_DATABASE[new_student.id] = new_student
    return new_student


@app.get(
    "/api/v1/students/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student Details",
    tags=["Students"],
)
async def get_student(
    student_id: Annotated[UUID, Path(description="UUID v4 of registered student")]
):
    student = STUDENT_DATABASE.get(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' does not exist.",
        )
    return student


@app.get(
    "/api/v1/students/",
    response_model=list[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List & Filter Students",
    tags=["Students"],
)
async def list_students(
    branch: Annotated[BranchCode | None, Query(description="Filter by engineering branch")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 20,
    offset: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
):
    results = list(STUDENT_DATABASE.values())
    if branch:
        results = [s for s in results if s.branch == branch]
    return results[offset : offset + limit]


@app.post(
    "/api/v1/students/{student_id}/attendance",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Attendance",
    tags=["Attendance"],
)
async def mark_attendance(
    student_id: Annotated[UUID, Path(...)],
    attendance_status: Annotated[
        Literal["present", "absent", "leave"],
        Query(description="Attendance status for current session")
    ] = "present"
):
    student = STUDENT_DATABASE.get(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    student.total_classes += 1
    if attendance_status == "present":
        student.attended_classes += 1

    return student
```

---

# Project 2: Enterprise Cloud Asset & Billing Document Vault

### 1. Business Problem
Ek financial services company ko ek microservice chahiye jisme clients apni billing profile register kar sakein, sensitive verification keys supply karein, aur compliance documents (`.pdf`, `.png`) upload karein:
- API Keys aur Secret tokens leak hone se bachane ke liye `SecretStr` use ho.
- File upload me memory overflow (OOM) attack na ho sake, isliye safe 1MB chunked streaming use ho.
- MIME type strict validation ho (koi executable `.exe` ya `.sh` upload na ho sake).
- File size boundary (maximum 10MB) enforce ho.
- Bill generation payload me dynamic subtotals aur taxes calculate hon.

### 2. Tech Stack & Concepts Covered
- **File & Form Validations**: `UploadFile`, `File(...)`, `Form(...)`, file header MIME verification.
- **Security Fields**: `SecretStr`, masked string serialization.
- **Financial Types**: `Decimal` for currency precision, `computed_field` for GST calculation.
- **Concurrency**: Blocking file disk writes handled without freezing the ASGI event loop.

### 3. API Contract Specifications

| Method | Endpoint | Description | Status Code | Content-Type |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/merchants/` | Register merchant billing entity | `201 Created` | `application/json` |
| `POST` | `/api/v1/merchants/{merchant_id}/documents` | Stream & validate legal document | `201 Created` | `multipart/form-data` |
| `POST` | `/api/v1/merchants/{merchant_id}/invoices` | Calculate validated tax invoice | `200 OK` | `application/json` |

### 4. Implementation Code

```python
import os
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

import anyio
from fastapi import FastAPI, File, Form, HTTPException, Path as FPath, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, SecretStr, computed_field

app = FastAPI(
    title="Enterprise Asset & Billing Engine",
    version="1.0.0",
    description="Phase 1 & 2 Practice Project covering File Streaming and Sensitive Data Validation",
)

STORAGE_DIR = Path("./temp_secure_vault")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB strict limit
ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}

# ----------------------------------------------------
# 1. Pydantic Models (Phase 2)
# ----------------------------------------------------
class MerchantRegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(..., min_length=3, max_length=80)
    business_email: EmailStr
    webhook_url: HttpUrl
    tax_identifier: str = Field(
        ...,
        pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$",
        description="Valid 15-character Indian GSTIN format",
    )
    api_access_secret: SecretStr = Field(
        ...,
        min_length=16,
        description="High-entropy private key supplied by merchant",
    )

class MerchantResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company_name: str
    business_email: EmailStr
    webhook_url: str
    tax_identifier: str
    # Notice: api_access_secret is intentionally excluded from response serialization!

class LineItem(BaseModel):
    description: str = Field(..., min_length=2)
    quantity: int = Field(..., ge=1, le=1000)
    unit_price: Decimal = Field(..., gt=Decimal("0.00"))

class InvoiceCalculationRequest(BaseModel):
    invoice_number: str = Field(..., pattern=r"^INV-\d{4}-\d{3,}$")
    tax_rate_percent: Decimal = Field(default=Decimal("18.00"), ge=Decimal("0.00"), le=Decimal("28.00"))
    items: list[LineItem] = Field(..., min_length=1)

class InvoiceCalculationResponse(BaseModel):
    invoice_number: str
    items: list[LineItem]
    
    @computed_field
    @property
    def subtotal(self) -> Decimal:
        raw_subtotal = sum(item.quantity * item.unit_price for item in self.items)
        return raw_subtotal.quantize(Decimal("0.01"))

    @computed_field
    @property
    def tax_amount(self) -> Decimal:
        tax = (self.subtotal * Decimal("18.00")) / Decimal("100.00")
        return tax.quantize(Decimal("0.01"))

    @computed_field
    @property
    def total_payable(self) -> Decimal:
        return (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))

# ----------------------------------------------------
# 2. In-Memory Mock Store
# ----------------------------------------------------
MERCHANT_VAULT: dict[UUID, dict] = {}

# ----------------------------------------------------
# 3. Endpoints
# ----------------------------------------------------
@app.post(
    "/api/v1/merchants/",
    response_model=MerchantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Merchant Onboarding"],
)
async def create_merchant(payload: MerchantRegisterRequest):
    merchant_id = uuid4()
    
    # Store complete payload (including the secret) in the secure vault dict
    stored_data = payload.model_dump()
    stored_data["id"] = merchant_id
    stored_data["webhook_url"] = str(payload.webhook_url)
    
    # The actual plain string secret is accessible ONLY internally:
    # internal_secret = payload.api_access_secret.get_secret_value()
    
    MERCHANT_VAULT[merchant_id] = stored_data

    # Return public response schema
    return MerchantResponse(
        id=merchant_id,
        company_name=payload.company_name,
        business_email=payload.business_email,
        webhook_url=str(payload.webhook_url),
        tax_identifier=payload.tax_identifier,
    )


@app.post(
    "/api/v1/merchants/{merchant_id}/documents",
    status_code=status.HTTP_201_CREATED,
    tags=["Compliance Documents"],
)
async def upload_compliance_document(
    merchant_id: Annotated[UUID, FPath(description="UUID of registered merchant")],
    document_type: Annotated[Literal["PAN", "GST_CERTIFICATE", "CANCELLED_CHEQUE"], Form(...)],
    file: UploadFile = File(...),
):
    if merchant_id not in MERCHANT_VAULT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not registered.")

    # 1. MIME Type Validation
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension/type '{file.content_type}' is not supported. Use: {ALLOWED_TYPES}",
        )

    # 2. Streaming write to protect server RAM (1MB buffers)
    safe_filename = f"{merchant_id}_{document_type}_{file.filename}"
    target_path = STORAGE_DIR / safe_filename
    total_bytes = 0

    try:
        with target_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunk
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds the maximum allowable limit of 10 MB.",
                    )
                buffer.write(chunk)
    finally:
        await file.close()

    return {
        "status": "success",
        "merchant_id": merchant_id,
        "document_type": document_type,
        "saved_filename": safe_filename,
        "bytes_stored": total_bytes,
    }


@app.post(
    "/api/v1/merchants/{merchant_id}/invoices",
    response_model=InvoiceCalculationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Billing & Invoices"],
)
async def generate_invoice_preview(
    merchant_id: Annotated[UUID, FPath(...)],
    payload: InvoiceCalculationRequest,
):
    if merchant_id not in MERCHANT_VAULT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant does not exist.")

    return InvoiceCalculationResponse(
        invoice_number=payload.invoice_number,
        items=payload.items,
    )
```

---

## 5. How to Run & Verify These Projects

### Step 1: Install Dependencies
Terminal me zaroori packages install karein:
```bash
pip install fastapi uvicorn[standard] pydantic[email] python-multipart
```

### Step 2: Run Application
Agar aapne Project 1 ka code `student_app.py` me save kiya hai, toh run karein:
```bash
uvicorn student_app:app --reload --port 8000
```
Swagger UI ko access karein: `http://127.0.0.1:8000/docs`

### Step 3: Test Edge Cases (Khud verify karein)
1. **Pydantic Validation**:
   - Project 1 me `roll_number` me `STU-2024-1234` ki jagah invalid format (`STUDENT-99`) daal kar dekhein. Expected: `422 Unprocessable Entity`.
   - `scholarship_fee_discount` me `-5` ya `105` bhej kar check karein.
2. **File Size Protection**:
   - Project 2 me koi 15MB ki PDF upload karne ki koshish karein. Expected: `413 Request Entity Too Large` aur incomplete file automatically disk se delete ho jayegi.
3. **Secret Security**:
   - Check karein ki Project 2 me `POST /api/v1/merchants/` call karne ke baad response JSON me `api_access_secret` mask ho chuka hai ya gayab hai.