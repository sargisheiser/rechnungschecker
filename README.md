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
│   ├── api/v1/           # API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── validate.py   # Validation endpoints
│   │   ├── convert.py    # Conversion endpoints
│   │   ├── templates.py  # Template management
│   │   ├── analytics.py  # Analytics dashboard
│   │   ├── webhooks.py   # Webhook management
│   │   ├── api_keys.py   # API key management
│   │   └── audit.py      # Audit logs
│   ├── core/             # Database, security, cache
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   └── services/
│       ├── validator/    # KoSIT validation
│       ├── converter/    # PDF to e-invoice conversion
│       ├── reports/      # PDF report generation
│       ├── email/        # Email delivery service
│       ├── billing/      # Stripe billing integration
│       └── audit/        # Audit logging service
├── alembic/              # Database migrations
├── frontend/             # React frontend (Vite + React 18)
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks (React Query)
│   │   ├── pages/        # Page components
│   │   ├── locales/      # i18n translations (de, en)
│   │   └── lib/          # API client, utilities
├── kosit/                # KoSIT validator (download separately)
├── test_files/           # Test files for validation
└── docker-compose.yml    # Docker services (PostgreSQL, Redis)
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
```

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

| Feature | Free | Pro | Steuerberater |
|---------|------|-----|---------------|
| Validations/month | 10 | 500 | Unlimited |
| Conversions/month | 5 | 200 | Unlimited |
| Batch Processing | - | ✓ | ✓ |
| Templates | - | ✓ | ✓ |
| Analytics | - | ✓ | ✓ |
| API Access | - | ✓ | ✓ |
| Webhooks | - | ✓ | ✓ |
| Client Management | - | - | ✓ |
| Priority Support | - | - | ✓ |

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
