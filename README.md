# RechnungsChecker

E-Invoice Validation & Conversion Platform for German SMEs and Steuerberater.

## Features

- **XRechnung Validation**: Validate XRechnung XML files against official KoSIT rules
- **ZUGFeRD Validation**: Validate ZUGFeRD PDF files (coming soon)
- **German Error Messages**: All validation errors in clear German with fix suggestions
- **PDF Reports**: Downloadable validation reports

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Java 11+ (for KoSIT validator)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/your-org/rechnungschecker.git
cd rechnungschecker
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Start services with Docker:
```bash
cd docker
docker-compose up -d db redis
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API is now available at http://localhost:8000

### Using Docker

```bash
cd docker
docker-compose up -d
```

## API Documentation

When running in development mode, API docs are available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/validate/xrechnung` | Validate XRechnung XML |
| POST | `/api/v1/validate/zugferd` | Validate ZUGFeRD PDF |
| GET | `/api/v1/reports/{id}/pdf` | Download validation report |
| GET | `/health` | Health check |

## Testing

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
rechnungschecker/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Database, security, exceptions
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── validator/    # Validation services
│   │   ├── converter/    # PDF conversion (future)
│   │   ├── reports/      # PDF report generation
│   │   └── billing/      # Stripe integration
│   └── utils/            # Utilities
├── alembic/              # Database migrations
├── docker/               # Docker configuration
├── kosit/                # KoSIT validator files
└── tests/                # Test suite
```

## License

Proprietary - All rights reserved.
