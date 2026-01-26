# RechnungsChecker

E-Invoice Validation & Conversion Platform for German SMEs and Steuerberater.

## Features

### Validation
- **XRechnung Validation**: Validate XRechnung XML files against official KoSIT rules
- **ZUGFeRD Validation**: Validate ZUGFeRD PDF/XML files with embedded invoice data
- **German Error Messages**: All validation errors in clear German with 170+ actionable fix suggestions
- **Batch Validation**: Validate multiple files at once (paid plans)
- **Validation History**: Browse and search past validations with detailed results
- **PDF Reports**: Downloadable validation reports

### PDF Conversion
- **PDF to E-Invoice Conversion**: Convert PDF invoices to XRechnung or ZUGFeRD format
- **Live PDF Preview**: See the original PDF while editing extracted data
- **AI-Powered Extraction**: OpenAI GPT-4o extracts invoice data from PDFs
- **Line Item Extraction**: Automatic extraction of invoice line items
- **Multiple VAT Rates**: Support for 19%, 7%, and 0% VAT rates
- **Auto-Validation**: Converted invoices are automatically validated with KoSIT
- **XML Preview**: Preview generated XML before download
- **Batch Conversion**: Convert multiple PDFs at once (Pro+)
- **Email Delivery**: Send converted invoices directly via email

### Templates & Workflow
- **Templates**: Save sender/receiver company data for quick invoice creation
- **Dashboard Quick Actions**: Quick access to common features
- **Client Management**: Manage multiple clients (Steuerberater plan)

### Integration & API
- **REST API**: Full API access for integration
- **API Keys**: Generate and manage API keys (Pro+)
- **Webhook Notifications**: Get notified about validation results
- **Audit Logging**: Track all actions for compliance

### Analytics & Monitoring
- **Analytics Dashboard**: View validation statistics and trends (Pro+)
- **Usage Tracking**: Monitor API usage and quotas
- **Langfuse Integration**: LLM observability for AI-powered features

### Authentication
- **Google OAuth**: Sign in with Google for frictionless registration
- **Email Verification**: 6-digit code verification
- **Password Reset**: Secure password recovery flow

### Team Features
- **Organizations**: Create teams with multiple users (Pro+)
- **Role-based Access**: Owner, Admin, Member roles
- **Member Invitations**: Invite team members via email
- **Shared Usage**: Team-wide validation quotas

### Invoice Creation
- **Invoice Wizard**: Create XRechnung invoices from scratch
- **Step-by-step Builder**: Guided form for all invoice fields
- **Auto-validation**: Generated invoices are validated with KoSIT
- **Draft Support**: Save and continue editing later

### Automation
- **Scheduled Validations**: Auto-validate files from AWS S3 (Pro+)
- **Cron Scheduling**: Daily, weekly, or custom schedules
- **Post-validation Actions**: Move or delete files after validation
- **Webhook Notifications**: Get notified when scheduled runs complete

### User Experience
- **Multi-language Support**: German and English UI (i18n)
- **Responsive Design**: Works on desktop and mobile
- **Dark Mode Ready**: UI components support theming

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Java 11+ (for KoSIT validator)

### 1. Clone the Repository

```bash
git clone https://github.com/sargisheiser/rechnungschecker.git
cd rechnungschecker
```

### 2. Download KoSIT Validator

The KoSIT validator is required for XRechnung/ZUGFeRD validation. Download and extract it:

```bash
# Create kosit directory
mkdir -p kosit

# Download KoSIT validator (v1.5.0)
curl -L -o kosit/validator.zip https://github.com/itplr-kosit/validator/releases/download/v1.5.0/validator-1.5.0-distribution.zip
unzip kosit/validator.zip -d kosit/
rm kosit/validator.zip

# Download XRechnung configuration
curl -L -o kosit/xrechnung-config.zip https://github.com/itplr-kosit/validator-configuration-xrechnung/releases/download/release-2024-11-19/validator-configuration-xrechnung_3.0.2_2024-11-19.zip
unzip kosit/xrechnung-config.zip -d kosit/
rm kosit/xrechnung-config.zip
```

### 3. Install Java (macOS)

```bash
# Using Homebrew
brew install openjdk

# Verify installation
/opt/homebrew/opt/openjdk/bin/java -version
```

### 4. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials
```

### 5. Database Setup

```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d db redis

# Run migrations
alembic upgrade head
```

### 6. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 7. Start Development Servers

**Backend** (Terminal 1):
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

The application is now available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## API Documentation

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Validation** | | |
| POST | `/api/v1/validate/` | Validate XRechnung/ZUGFeRD (authenticated) |
| POST | `/api/v1/validate/guest` | Validate as guest (limited) |
| POST | `/api/v1/validate/zugferd` | Validate ZUGFeRD PDF |
| POST | `/api/v1/validate/batch` | Batch validate multiple files |
| GET | `/api/v1/validate/history` | Get validation history |
| **Conversion** | | |
| POST | `/api/v1/convert/preview` | Preview PDF extraction |
| POST | `/api/v1/convert/` | Convert PDF to e-invoice |
| POST | `/api/v1/convert/batch` | Batch convert multiple PDFs |
| POST | `/api/v1/convert/{id}/send-email` | Send converted invoice via email |
| GET | `/api/v1/convert/status` | Get conversion service status |
| **Reports** | | |
| GET | `/api/v1/reports/{id}/pdf` | Download validation report |
| **Templates** | | |
| GET | `/api/v1/templates/` | List saved templates |
| POST | `/api/v1/templates/` | Create new template |
| PUT | `/api/v1/templates/{id}` | Update template |
| DELETE | `/api/v1/templates/{id}` | Delete template |
| **Analytics** | | |
| GET | `/api/v1/analytics/overview` | Get analytics overview |
| GET | `/api/v1/analytics/validations` | Get validation statistics |
| GET | `/api/v1/analytics/conversions` | Get conversion statistics |
| **Webhooks** | | |
| GET | `/api/v1/webhooks/` | List webhooks |
| POST | `/api/v1/webhooks/` | Create webhook |
| DELETE | `/api/v1/webhooks/{id}` | Delete webhook |
| **API Keys** | | |
| GET | `/api/v1/api-keys/` | List API keys |
| POST | `/api/v1/api-keys/` | Create API key |
| DELETE | `/api/v1/api-keys/{id}` | Revoke API key |
| **Audit** | | |
| GET | `/api/v1/audit/logs` | Get audit logs |
| **Organizations** | | |
| GET | `/api/v1/organizations/` | List user's organizations |
| POST | `/api/v1/organizations/` | Create organization |
| POST | `/api/v1/organizations/{id}/members` | Invite member |
| DELETE | `/api/v1/organizations/{id}/members/{uid}` | Remove member |
| **Invoice Creator** | | |
| GET | `/api/v1/invoices/drafts/` | List invoice drafts |
| POST | `/api/v1/invoices/drafts/` | Create new draft |
| PATCH | `/api/v1/invoices/drafts/{id}` | Update draft |
| POST | `/api/v1/invoices/drafts/{id}/generate` | Generate XRechnung |
| GET | `/api/v1/invoices/drafts/{id}/preview` | Preview XML |
| **Scheduled Validations** | | |
| GET | `/api/v1/scheduled-validations/` | List scheduled jobs |
| POST | `/api/v1/scheduled-validations/` | Create scheduled job |
| PATCH | `/api/v1/scheduled-validations/{id}` | Update job |
| DELETE | `/api/v1/scheduled-validations/{id}` | Delete job |
| POST | `/api/v1/scheduled-validations/{id}/run` | Trigger manual run |
| GET | `/api/v1/scheduled-validations/{id}/runs` | Get run history |
| **OAuth** | | |
| GET | `/api/v1/auth/google/login` | Initiate Google OAuth |
| POST | `/api/v1/auth/google/callback` | Google OAuth callback |

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

### Validation Example

```bash
# Guest validation (limited to 1 per day)
curl -X POST http://localhost:8000/api/v1/validate/guest \
  -F "file=@invoice.xml"

# Authenticated validation
curl -X POST http://localhost:8000/api/v1/validate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@invoice.xml"
```

### API Error Codes

The API returns structured error responses for certain errors:

| Code | Description |
|------|-------------|
| `VALIDATION_LIMIT_REACHED` | Monthly validation quota exceeded |
| `CONVERSION_LIMIT_REACHED` | Monthly conversion quota exceeded |
| `GUEST_LIMIT_REACHED` | Guest validation limit (1/day) exceeded |
| `AUTH_INVALID_CREDENTIALS` | Invalid email or password |
| `AUTH_EMAIL_NOT_VERIFIED` | Email address not verified |
| `AUTH_TOKEN_EXPIRED` | Session token has expired |
| `AUTHZ_PLAN_REQUIRED` | Feature requires plan upgrade |
| `NOT_FOUND` | Resource not found |
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit |

Error response format:
```json
{
  "detail": {
    "code": "VALIDATION_LIMIT_REACHED",
    "message": "Sie haben Ihr monatliches Limit erreicht.",
    "validations_used": 100,
    "validations_limit": 100
  }
}
```

## Testing

Test files are included in the `test_files/` directory:

```bash
# Run validation tests
pytest

# Test with coverage
pytest --cov=app --cov-report=html

# Manual testing with test files
curl -X POST http://localhost:8000/api/v1/validate/guest \
  -F "file=@test_files/xrechnung/valid_xrechnung.xml" \
  -F "guest_id=test-123"
```

### Test Files

| File | Type | Expected Result |
|------|------|-----------------|
| `test_files/xrechnung/valid_xrechnung.xml` | XRechnung | Valid |
| `test_files/xrechnung/invalid_missing_buyer_reference.xml` | XRechnung | Invalid (4 errors) |
| `test_files/xrechnung/invalid_malformed_xml.xml` | XRechnung | Invalid (XML parse error) |
| `test_files/zugferd/valid_zugferd_en16931.xml` | ZUGFeRD | Valid |
| `test_files/pdf_conversion/valid_invoice.pdf` | PDF | For conversion testing |

## Project Structure

```
rechnungschecker/
├── app/
│   ├── api/v1/                    # API endpoints
│   │   ├── auth.py                # Authentication (incl. Google OAuth)
│   │   ├── validate.py            # Validation endpoints
│   │   ├── convert.py             # Conversion endpoints
│   │   ├── templates.py           # Template management
│   │   ├── invoices.py            # Invoice creator wizard
│   │   ├── organizations.py       # Team/organization management
│   │   ├── scheduled_validations.py  # Scheduled S3 validations
│   │   ├── analytics.py           # Analytics dashboard
│   │   ├── webhooks.py            # Webhook management
│   │   ├── api_keys.py            # API key management
│   │   └── audit.py               # Audit logs
│   ├── core/                      # Database, security, cache, i18n
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic schemas
│   └── services/
│       ├── validator/             # KoSIT validation
│       ├── converter/             # PDF to e-invoice conversion
│       ├── invoice_creator/       # XRechnung XML generation
│       ├── scheduler/             # APScheduler for cron jobs
│       ├── storage/               # Cloud storage (S3) client
│       ├── oauth/                 # Google OAuth service
│       ├── reports/               # PDF report generation
│       ├── email/                 # Email delivery service
│       ├── billing/               # Stripe billing integration
│       └── audit/                 # Audit logging service
├── alembic/                       # Database migrations
├── frontend/                      # React frontend (Vite + React 18)
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── hooks/                 # Custom hooks (React Query)
│   │   ├── pages/                 # Page components
│   │   ├── locales/               # i18n translations (de, en)
│   │   └── lib/                   # API client, utilities
├── kosit/                         # KoSIT validator (download separately)
├── tests/                         # Pytest test files
├── test_files/                    # Test files for validation
└── docker-compose.yml             # Docker services (PostgreSQL, Redis)
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rechnungschecker

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# KoSIT (paths relative to project root)
KOSIT_JAR_PATH=kosit/validationtool-1.5.0-standalone.jar
KOSIT_SCENARIOS_PATH=kosit/scenarios.xml

# Google OAuth (optional)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# OpenAI (for PDF conversion)
OPENAI_API_KEY=your-openai-api-key

# Email (Mailgun)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-mailgun-domain

# Stripe (for billing)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### Google OAuth Setup (Optional)

To enable Google OAuth login:

1. Create a Google Cloud project at https://console.cloud.google.com
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 credentials (Web application type)
4. Add authorized redirect URIs:
   - Development: `http://localhost:3000/auth/google/callback`
   - Production: `https://your-domain.com/auth/google/callback`
5. Add the client ID and secret to your `.env` file

## Troubleshooting

### Java not found
```bash
# macOS with Homebrew
brew install openjdk
# The app automatically finds Java in /opt/homebrew/opt/openjdk/bin/java
```

### Database connection errors
```bash
# Ensure PostgreSQL is running
docker-compose up -d db

# Check connection
psql postgresql://user:password@localhost:5432/rechnungschecker
```

### KoSIT validation fails
```bash
# Verify KoSIT files exist
ls -la kosit/*.jar kosit/scenarios.xml

# Test KoSIT manually
/opt/homebrew/opt/openjdk/bin/java -jar kosit/validationtool-1.5.0-standalone.jar \
  -s kosit/scenarios.xml -r kosit test_files/xrechnung/valid_xrechnung.xml
```

## Pricing Plans

| Feature | Free | Starter | Pro | Steuerberater |
|---------|------|---------|-----|---------------|
| Validations/month | 10 | 100 | 500 | Unlimited |
| Conversions/month | 5 | 50 | 200 | Unlimited |
| Invoice Creator | - | ✓ | ✓ | ✓ |
| Templates | - | ✓ | ✓ | ✓ |
| Batch Processing | - | - | ✓ | ✓ |
| Scheduled Validations | - | - | ✓ | ✓ |
| Teams/Organizations | - | - | ✓ | ✓ |
| Analytics Dashboard | - | - | ✓ | ✓ |
| API Access | - | - | ✓ | ✓ |
| Webhooks | - | - | ✓ | ✓ |
| Client Management | - | - | - | ✓ |
| Priority Support | - | - | - | ✓ |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, React Query
- **Validation**: KoSIT Validator (Java)
- **AI**: OpenAI GPT-4o for PDF extraction
- **Email**: Mailgun
- **Payments**: Stripe
- **Caching**: Redis
- **Monitoring**: Langfuse (LLM observability)

## License

Proprietary - All rights reserved.
