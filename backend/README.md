# Options Trading API - Clean Architecture

A modern FastAPI backend for options trading with clean, async-ready architecture.

## Architecture Overview

This application follows a clean, layered architecture:

```
app/
├── api/                    # HTTP layer (thin)
│   └── v1/
│       ├── router.py       # Main API router
│       └── routers/        # Feature routers
├── core/                   # Core configuration
│   ├── config.py          # Settings & configuration
│   ├── deps.py            # Dependency injection
│   └── errors.py          # Error definitions
├── domain/                # Business domain
│   ├── models.py          # ORM models
│   └── errors.py          # Domain errors
├── schemas/               # Pydantic DTOs
│   └── watchlist.py       # Request/response schemas
├── services/              # Business logic layer
│   └── watchlist_service.py
├── repositories/          # Data access interfaces
│   ├── watchlist_repo.py  # Repository protocols
│   └── sqlalchemy/        # SQLAlchemy implementations
├── infrastructure/        # External concerns
│   ├── db.py              # Database setup
│   └── migrations/        # Alembic migrations
└── tests/                 # Test suite
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    └── api/               # API tests
```

## Key Features

- **Async-first**: Uses async SQLAlchemy with aiosqlite for scalable I/O
- **Clean Architecture**: Clear separation of concerns across layers
- **Type Safety**: Full Pydantic v2 integration for request/response validation
- **Error Handling**: Consistent typed errors mapped to HTTP responses
- **Testing**: Comprehensive test coverage with unit, integration, and API tests
- **Migrations**: Alembic for database schema management

## Quick Start

### Prerequisites

- Python 3.11+
- SQLite (included)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Initialize database:
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

4. Run the application:
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Adding a New Feature

Follow this pattern for new features:

1. **Domain Model**: Add ORM model in `app/domain/models.py`
2. **Schemas**: Create Pydantic schemas in `app/schemas/<feature>.py`
3. **Repository**: Define interface in `app/repositories/<feature>_repo.py`
4. **Repository Implementation**: Implement in `app/repositories/sqlalchemy/<feature>_repo.py`
5. **Service**: Add business logic in `app/services/<feature>_service.py`
6. **API Router**: Create endpoints in `app/api/v1/routers/<feature>.py`
7. **Tests**: Add unit, integration, and API tests

### Example: Watchlist Feature

The watchlist feature demonstrates the complete pattern:

- **Models**: `TickerWatchlist`, `OptionWatchlist`
- **Schemas**: `TickerWatchlistCreate`, `TickerWatchlistResponse`
- **Repository**: `TickerWatchlistRepository` (Protocol)
- **Implementation**: `SqlAlchemyTickerWatchlistRepository`
- **Service**: `WatchlistService`
- **API**: `/api/v1/watchlist/*` endpoints

### Database Migrations

Create new migrations:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1
```

### Testing

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest app/tests/unit/          # Unit tests only
pytest app/tests/api/            # API tests only
pytest app/tests/integration/    # Integration tests only
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Configuration

Key settings in `app/core/config.py`:

- `database_url`: SQLite database connection string
- `cors_origins`: Allowed CORS origins
- `debug`: Enable debug mode
- `api_v1_prefix`: API version prefix

Environment variables override defaults (see `.env.example`).

## Error Handling

The application uses typed domain errors:

- `NotFoundError`: Resource not found (404)
- `ConflictError`: Resource conflict (409)
- `ValidationError`: Invalid input (400)
- `UnauthorizedError`: Authentication required (401)
- `ForbiddenError`: Insufficient permissions (403)
- `ExternalServiceError`: Third-party service failure (502)
- `DatabaseError`: Database operation failure (500)

All errors return consistent JSON responses:
```json
{
  "error": "NotFoundError",
  "message": "Ticker AAPL not found in watchlist",
  "details": {}
}
```

## Migration from Legacy

This new architecture replaces the monolithic `main.py` approach:

1. **Incremental Migration**: Features are migrated one by one
2. **Parallel Development**: New architecture runs alongside legacy
3. **Feature Parity**: Each feature maintains full compatibility
4. **Clean Separation**: No mixed responsibilities within layers

The watchlist feature is the first complete migration and serves as the template for remaining features.

## Production Considerations

- Use PostgreSQL with `asyncpg` for production databases
- Configure proper logging and monitoring
- Set up API rate limiting
- Add authentication/authorization
- Configure reverse proxy (nginx)
- Set up process manager (systemd/supervisor)

## License

[Your License Here]