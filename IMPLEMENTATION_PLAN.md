# RechnungsChecker - Implementation Plan

**Version:** 1.0
**Date:** January 2026
**Status:** Awaiting Approval

---

## A) Source Documents

| File | Description |
|------|-------------|
| `rechnungschecker_commercial_docs.docx` | Complete commercial documentation (Business Plan, PRD, Technical Architecture, Go-to-Market) |

---

## B) MVP Understanding

### Project Goal

Web-based SaaS platform enabling German SMEs and Steuerberater to **validate** incoming e-invoices (XRechnung/ZUGFeRD) against legal requirements and **convert** PDF invoices to compliant formats.

### Target Users

| Persona | Description | Primary Need |
|---------|-------------|--------------|
| Buchhalterin (Maria) | Accountant at SME, 80 employees | Verify if received e-invoices are compliant |
| Steuerberater (Thomas) | Tax advisor, 150 clients | Batch validation, client reports |
| Geschäftsführer (Stefan) | Small business owner | Convert PDFs to XRechnung by 2027 |

### Functional Requirements (MVP)

| ID | Feature | Description |
|----|---------|-------------|
| FR-1 | XRechnung Validation | Upload XML, validate against KoSIT Schematron (XRechnung 3.0.x), return German error messages |
| FR-2 | ZUGFeRD Validation | Upload PDF, extract embedded XML, validate against ZUGFeRD 2.1.1/2.2 profiles |
| FR-3 | Validation Reports | Web UI results display, downloadable PDF reports with German explanations |
| FR-4 | PDF Conversion | OCR-based extraction, field mapping, user review wizard, XRechnung XML generation |
| FR-5 | User Management | Registration, guest mode (5 validations via IP tracking), dashboard, history |
| FR-6 | Billing | Stripe integration, Free/Starter(€29)/Pro(€79)/Steuerberater(€199) plans |

### Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Validation response time | <5 seconds |
| Performance | Conversion response time | <30 seconds |
| Availability | Uptime SLA | 99.5% monthly |
| Security | Data encryption | TLS 1.3 in transit, AES-256 at rest |
| Security | Invoice retention | No retention; deleted after processing |
| Compliance | DSGVO | Full compliance, German DPA jurisdiction |
| Compliance | Hosting | German/EU data center only |
| Scalability | Concurrent users | 100+ simultaneous validations |
| Localization | Languages | German (primary), English (secondary) |

### Explicit Tech Stack (from document)

- **Backend:** Python FastAPI
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **Database:** PostgreSQL
- **Cache/Queue:** Redis
- **Validation Engine:** KoSIT Validator (Java) - requires wrapper
- **OCR:** Tesseract 5 + pdf2image
- **PDF Processing:** PyMuPDF (fitz)
- **Payments:** Stripe
- **Hosting:** Hetzner Cloud (German DC)

### Constraints & Assumptions

- Solo developer, 4-5 week MVP timeline
- ~€58/month infrastructure budget
- No data retention by design
- Must work standalone (not tied to any ERP)

### Out of Scope (MVP)

| Feature | Target Version |
|---------|----------------|
| API access | V1.5 |
| Multi-client Steuerberater management | V1.5 |
| White-label options | V1.5 |
| DATEV export / accounting integrations | V2.0 |
| Invoice management, archiving, analytics | V3.0 |

---

## C) Open Questions / Technical Risks

### Ambiguities Requiring Clarification

#### 1. KoSIT Validator Integration
Document specifies Java-based KoSIT validator. Options:

| Option | Pros | Cons |
|--------|------|------|
| A: Java JAR via subprocess | Official validator, guaranteed compliance | Adds Java dependency (~500MB), subprocess overhead |
| B: Separate microservice | Clean separation, scalable | More infrastructure, complexity |
| C: Python-native Schematron (lxml) | No Java dependency | May lack official rule parity, maintenance burden |

**Recommendation:** Option A (subprocess) for MVP - compliance guaranteed, acceptable overhead.

#### 2. German Error Message Source
Document mentions "80+ rules" with German explanations. Sources:

- Manual curation from KoSIT documentation
- Community translations (if available)
- AI-assisted initial mapping with manual review

**Recommendation:** Manual curation from official KoSIT rule descriptions.

#### 3. Guest IP Tracking
IP-based limit for free tier has limitations:

| Method | Pros | Cons |
|--------|------|------|
| IP only | Simple, no cookies | Shared IPs, VPNs bypass |
| IP + Cookie | More reliable | Users can clear cookies |
| IP + Fingerprint | Most robust | Privacy concerns, complexity |

**Recommendation:** IP + secure cookie hybrid for MVP.

#### 4. ZUGFeRD Profile Support
Document mentions 2.1.1 and 2.2 versions. Profiles to support:

| Profile | Support Level |
|---------|---------------|
| MINIMUM | Validate with warning (deprecated) |
| BASIC-WL | Validate with warning (deprecated) |
| BASIC | Full support |
| EN 16931 (COMFORT) | Full support |
| EXTENDED | Full support |

#### 5. PDF Conversion Scope (MVP)
OCR accuracy varies significantly between document types:

| Document Type | OCR Accuracy | MVP Support |
|---------------|--------------|-------------|
| Digitally-generated PDFs | High (95%+) | Yes |
| High-quality scans | Medium (80-90%) | Limited |
| Low-quality scans | Low (<70%) | No |

**Recommendation:** MVP supports digitally-generated PDFs only, with clear disclaimers.

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| KoSIT rules change frequently | High | Medium | Automate rule updates, version display in reports |
| PDF/OCR accuracy issues | High | Medium | Confidence scores, mandatory user review, disclaimers |
| Java dependency complexity | Medium | Medium | Docker container for KoSIT |
| ZUGFeRD XML extraction edge cases | Medium | Medium | Test with diverse real-world samples |
| Solo dev burnout | Medium | High | Strict MVP scope, ship validation first |

---

## D) Python-Based Implementation Plan

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                     React 18 + TypeScript + Tailwind                    │
│                          (Hetzner CDN)                                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Auth     │  │  Validation │  │  Conversion │  │   Reports   │    │
│  │   Module    │  │   Service   │  │   Service   │  │   Service   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Billing   │  │    User     │  │   Storage   │  │    Rate     │    │
│  │  (Stripe)   │  │ Management  │  │   (Temp)    │  │  Limiting   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└───────────┬─────────────┬─────────────┬─────────────┬───────────────────┘
            │             │             │             │
            ▼             ▼             ▼             ▼
     ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
     │PostgreSQL │ │   Redis   │ │ Hetzner   │ │  KoSIT    │
     │           │ │ (sessions │ │ S3 (temp  │ │ Validator │
     │           │ │  & queue) │ │  files)   │ │  (Java)   │
     └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

### Python Framework & Libraries

| Purpose | Library | Version | Justification |
|---------|---------|---------|---------------|
| Web Framework | FastAPI | 0.109+ | Async, auto-docs, excellent for API-first |
| ASGI Server | Uvicorn | 0.27+ | Standard FastAPI deployment |
| ORM | SQLAlchemy | 2.0+ | Async support, mature, well-documented |
| Migrations | Alembic | 1.13+ | SQLAlchemy companion |
| Auth/JWT | python-jose | 3.3+ | JWT handling |
| Password Hashing | passlib[bcrypt] | 1.7+ | Secure password hashing |
| PDF Parsing | PyMuPDF | 1.23+ | ZUGFeRD XML extraction |
| OCR | pytesseract | 0.3+ | Tesseract wrapper |
| PDF to Image | pdf2image | 1.16+ | PDF page rendering |
| XML Processing | lxml | 5.0+ | XRechnung generation, XPath |
| PDF Reports | weasyprint | 60+ | HTML to PDF, German support |
| Payments | stripe | 7.0+ | Official Stripe SDK |
| Validation | subprocess | stdlib | KoSIT JAR execution |
| Task Queue | arq | 0.25+ | Async Redis-based jobs |
| HTTP Client | httpx | 0.26+ | Async HTTP requests |
| Settings | pydantic-settings | 2.0+ | Environment configuration |
| Testing | pytest | 8.0+ | Test framework |
| Async Testing | pytest-asyncio | 0.23+ | Async test support |

### Project Structure

```
rechnungschecker/
├── docker/
│   ├── Dockerfile              # Main application
│   ├── Dockerfile.validator    # KoSIT Java validator
│   └── docker-compose.yml      # Local development
├── alembic/
│   ├── versions/               # Database migrations
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Settings, environment variables
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py             # User, subscription, usage
│   │   └── validation.py       # ValidationLog (anonymized)
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py             # Login, registration
│   │   ├── validation.py       # Request/response models
│   │   ├── conversion.py       # Conversion flow models
│   │   └── billing.py          # Plan, subscription
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # API router aggregation
│   │       ├── auth.py         # /auth/* endpoints
│   │       ├── validate.py     # /validate/* endpoints
│   │       ├── convert.py      # /convert/* endpoints
│   │       ├── reports.py      # /reports/* endpoints
│   │       └── billing.py      # /billing/* endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validator/
│   │   │   ├── __init__.py
│   │   │   ├── kosit.py        # KoSIT JAR wrapper
│   │   │   ├── xrechnung.py    # XRechnung validation
│   │   │   └── zugferd.py      # ZUGFeRD extraction + validation
│   │   ├── converter/
│   │   │   ├── __init__.py
│   │   │   ├── ocr.py          # Tesseract OCR service
│   │   │   ├── extractor.py    # Field extraction, mapping
│   │   │   └── generator.py    # XRechnung XML generation
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── pdf.py          # PDF report generation
│   │   │   └── templates/      # German report templates
│   │   └── billing/
│   │       ├── __init__.py
│   │       └── stripe.py       # Stripe service layer
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── errors.py           # German error message mapping
│   │   ├── limits.py           # Rate limiting, usage tracking
│   │   └── exceptions.py       # Custom exceptions
│   └── utils/
│       ├── __init__.py
│       ├── storage.py          # Temporary file handling
│       └── xml.py              # XML utilities
├── kosit/
│   ├── validator.jar           # KoSIT validator
│   ├── scenarios/              # Validation scenarios
│   └── resources/              # Schematron rules
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_validation.py
│   ├── test_conversion.py
│   ├── test_auth.py
│   └── fixtures/               # Test XML/PDF files
├── .env.example
├── .gitignore
├── pyproject.toml              # Project dependencies
├── alembic.ini
└── README.md
```

### Data Models

#### User Model

```python
class User(Base):
    __tablename__ = "users"

    id: UUID                          # Primary key
    email: str                        # Unique, indexed
    password_hash: str                # bcrypt hash
    is_active: bool                   # Account status
    is_verified: bool                 # Email verified

    # Subscription
    plan: PlanType                    # free, starter, pro, steuerberater
    stripe_customer_id: str | None    # Stripe reference
    stripe_subscription_id: str | None
    plan_valid_until: datetime | None # For annual plans

    # Usage tracking (reset monthly)
    validations_this_month: int       # Default 0
    conversions_this_month: int       # Default 0
    usage_reset_date: date            # First of month

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
```

#### Guest Usage Model

```python
class GuestUsage(Base):
    __tablename__ = "guest_usage"

    id: UUID
    ip_address: str                   # Indexed
    cookie_id: str | None             # Secondary tracking
    validations_used: int             # Max 5
    first_validation_at: datetime
    last_validation_at: datetime
```

#### Validation Log Model (Anonymized)

```python
class ValidationLog(Base):
    __tablename__ = "validation_logs"

    id: UUID
    user_id: UUID | None              # Nullable for guests

    # Validation details (no content stored)
    file_type: FileType               # xrechnung, zugferd
    file_hash: str                    # SHA256 for deduplication stats
    file_size_bytes: int

    # Results
    is_valid: bool
    error_count: int
    warning_count: int
    info_count: int

    # Performance
    processing_time_ms: int
    validator_version: str            # KoSIT version used

    created_at: datetime
```

### API Endpoints

#### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new user account |
| POST | `/login` | Authenticate, return JWT |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate refresh token |
| POST | `/verify-email` | Email verification |
| POST | `/forgot-password` | Password reset request |
| POST | `/reset-password` | Password reset confirmation |

#### Validation (`/api/v1/validate`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/xrechnung` | Validate XRechnung XML |
| POST | `/zugferd` | Validate ZUGFeRD PDF |
| POST | `/batch` | Validate multiple files (paid plans) |
| GET | `/history` | User's validation history |

#### Conversion (`/api/v1/convert`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/extract` | Extract fields from PDF |
| POST | `/generate` | Generate XRechnung from reviewed data |
| GET | `/download/{id}` | Download generated file |

#### Reports (`/api/v1/reports`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{id}` | Get validation report |
| GET | `/{id}/pdf` | Download PDF report |

#### Billing (`/api/v1/billing`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plans` | List available plans |
| GET | `/subscription` | Current subscription details |
| POST | `/checkout` | Create Stripe checkout session |
| POST | `/portal` | Create Stripe billing portal session |
| POST | `/webhook` | Stripe webhook handler |

#### User (`/api/v1/user`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Current user profile |
| PATCH | `/me` | Update profile |
| GET | `/usage` | Current usage stats |
| DELETE | `/me` | Delete account (DSGVO) |

### Development Phases

#### Phase 1: Foundation (Week 1)

**Goals:** Project setup, database, KoSIT integration, basic XRechnung validation

| Day | Tasks |
|-----|-------|
| 1 | Project scaffold (FastAPI, Docker, CI/CD) |
| 1 | PostgreSQL + Redis setup, Alembic init |
| 2 | User and ValidationLog models, migrations |
| 2 | KoSIT validator download and Docker setup |
| 3 | KoSIT subprocess wrapper implementation |
| 3 | XRechnung validation service |
| 4 | `/validate/xrechnung` endpoint |
| 4 | Basic error handling, logging |
| 5 | Unit tests for validation service |
| 5 | Integration test with real XRechnung samples |

**Deliverable:** Working XRechnung validation via API

#### Phase 2: ZUGFeRD + Error Mapping (Week 2)

**Goals:** ZUGFeRD support, German error messages, validation history

| Day | Tasks |
|-----|-------|
| 1 | ZUGFeRD PDF parsing (PyMuPDF XML extraction) |
| 1 | ZUGFeRD profile detection |
| 2 | ZUGFeRD validation service |
| 2 | `/validate/zugferd` endpoint |
| 3 | German error message mapping (KoSIT rules) |
| 3 | Error categorization (error/warning/info) |
| 4 | Validation result formatting |
| 4 | Validation history storage |
| 5 | Tests with various ZUGFeRD samples |
| 5 | Edge case handling |

**Deliverable:** Complete validation for both formats with German messages

#### Phase 3: Reports + User Management (Week 3)

**Goals:** PDF reports, authentication, guest tracking, dashboard

| Day | Tasks |
|-----|-------|
| 1 | PDF report template (German, WeasyPrint) |
| 1 | Report generation service |
| 2 | `/reports/{id}` and `/reports/{id}/pdf` endpoints |
| 2 | User registration, email verification |
| 3 | JWT authentication (login, refresh, logout) |
| 3 | Password reset flow |
| 4 | Guest usage tracking (IP + cookie) |
| 4 | Rate limiting implementation |
| 5 | User dashboard endpoints |
| 5 | Usage tracking and limits |

**Deliverable:** Full user system with reports

#### Phase 4: Billing + PDF Conversion (Week 4)

**Goals:** Stripe subscriptions, plan limits, basic PDF conversion

| Day | Tasks |
|-----|-------|
| 1 | Stripe integration setup |
| 1 | Checkout session creation |
| 2 | Webhook handling (subscription events) |
| 2 | Plan limit enforcement |
| 3 | Tesseract OCR setup and service |
| 3 | PDF field extraction |
| 4 | Field mapping to XRechnung schema |
| 4 | `/convert/extract` endpoint |
| 5 | XRechnung XML generation |
| 5 | `/convert/generate` endpoint |

**Deliverable:** Monetizable product with basic conversion

#### Phase 5: Polish + Launch (Week 5)

**Goals:** Hardening, legal compliance, soft launch

| Day | Tasks |
|-----|-------|
| 1 | Comprehensive error handling |
| 1 | Input validation hardening |
| 2 | Security review (OWASP checklist) |
| 2 | Temporary file cleanup verification |
| 3 | API documentation (OpenAPI/Swagger) |
| 3 | Legal endpoints (Impressum, Datenschutz) |
| 4 | Load testing, performance optimization |
| 4 | Monitoring setup (Sentry) |
| 5 | Beta user onboarding |
| 5 | Soft launch |

**Deliverable:** Production-ready MVP

---

## E) Infrastructure

### Hosting (Hetzner Cloud)

| Component | Specification | Cost/Month |
|-----------|---------------|------------|
| App Server | CX31 (4 vCPU, 8GB RAM) | €15 |
| Database | CX11 + PostgreSQL | €8 |
| Redis | CX11 | €5 |
| Object Storage | 100GB S3-compatible | €5 |
| Validator | CX21 (Java runtime) | €10 |
| **Total** | | **~€43** |

### External Services

| Service | Purpose | Cost/Month |
|---------|---------|------------|
| Mailgun | Transactional email | €15 |
| Sentry | Error monitoring | €0 (dev tier) |
| Stripe | Payments | 1.4% + €0.25/transaction |
| Cloudflare | DNS, DDoS protection | €0 (free tier) |
| Let's Encrypt | SSL certificates | €0 |

### Total Infrastructure: ~€58/month

---

## F) Security Checklist

| Category | Requirement | Implementation |
|----------|-------------|----------------|
| Transport | TLS 1.3 | Let's Encrypt + Nginx |
| Authentication | JWT tokens | 15min access, 7-day refresh |
| Passwords | Secure hashing | bcrypt with salt |
| File Handling | No retention | Auto-delete after processing |
| API Security | Rate limiting | 100 req/min guest, 1000 auth |
| Database | Query safety | SQLAlchemy parameterized queries |
| Secrets | Secure storage | Environment variables |
| CORS | Restricted | App domain only |
| Audit | Logging | Anonymized validation logs |

---

## G) Acceptance Criteria

### MVP Launch Criteria

- [ ] XRechnung XML validation works with <5s response time
- [ ] ZUGFeRD PDF validation works with <5s response time
- [ ] German error messages for all KoSIT rules
- [ ] PDF validation report downloadable
- [ ] User registration and authentication functional
- [ ] Guest mode allows 5 free validations
- [ ] Stripe subscription checkout works
- [ ] Plan limits enforced correctly
- [ ] Basic PDF-to-XRechnung conversion functional
- [ ] No invoice data retained after processing
- [ ] DSGVO-compliant privacy policy in place
- [ ] Impressum and AGB published
- [ ] 99%+ uptime during soft launch week

---

## H) Recommended Decisions

Based on the analysis, the following defaults are recommended:

| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| KoSIT Integration | Java JAR via subprocess | Compliance guaranteed, acceptable overhead |
| Error Messages | Manual curation | Quality control, accuracy |
| Guest Tracking | IP + secure cookie | Balance of reliability and privacy |
| ZUGFeRD Profiles | BASIC and above | Deprecated profiles get warnings |
| PDF Conversion | Digital PDFs only (MVP) | OCR accuracy, clear scope |

---

## I) Next Steps

1. **Review and approve** this implementation plan
2. **Clarify** any open questions marked above
3. **Confirm** technology choices (especially KoSIT approach)
4. **Begin Phase 1** development

---

*Document generated from analysis of `rechnungschecker_commercial_docs.docx`*
