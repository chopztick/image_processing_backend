# Image Processing Service

A cloud-native backend service for image processing with vector-based similarity search capabilities. Built with FastAPI and PostgreSQL with pgvector extension.

## 🎯 Features

- **Image Upload & Processing**: Accept image uploads (JPEG/PNG) with validation and metadata extraction
- **Mock Embedding Generation**: Consistent hash-based vector embeddings for demonstration
- **Vector Similarity Search**: Find similar images using pgvector cosine similarity
- **RESTful API**: Comprehensive API with OpenAPI/Swagger documentation
- **Async Processing**: Non-blocking file handling with FastAPI
- **Cloud-Native Design**: Containerized with Docker and Docker Compose
- **Health Checks**: Multiple health check endpoints for monitoring
- **Comprehensive Testing**: Full test suite with pytest

## 🏗️ Architecture

### Technology Stack

- **Backend Framework**: FastAPI with async support
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0 (async)
- **Image Processing**: Pillow (PIL)
- **Validation**: Pydantic v2
- **Containerization**: Docker + Docker Compose
- **Testing**: pytest with asyncio support

### Project Structure

```
image_processing_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application setup
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── images.py          # Image endpoints
│   │       └── health.py          # Health check endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration settings
│   │   └── database.py            # Database setup and session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── image.py               # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── image.py               # Pydantic schemas
│   └── services/
│       ├── __init__.py
│       ├── image_processing.py    # Image processing and mock embeddings
│       └── vector_service.py      # pgvector operations
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Test configuration and fixtures
│   ├── test_api/
│   │   ├── test_images.py         # API endpoint tests
│   │   └── test_health.py         # Health check tests
│   └── test_services/
│       └── test_image_processing.py # Service layer tests
├── docker-compose.yml             # Multi-service deployment
├── Dockerfile                     # API service container
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── init.sql                      # Database initialization
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project directory**:
   ```bash
   cd image_processing_backend
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```
   
   > **Note**: The PostgreSQL service uses port `5433` to avoid conflicts with existing PostgreSQL installations. If you encounter port conflicts, see the [Port Conflicts](#port-conflicts) section below.

3. **Verify the services are running**:
   ```bash
   # Check service health
   curl http://localhost:8000/api/v1/health
   
   # View API documentation
   open http://localhost:8000/docs
   ```

### Local Development Setup

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL with pgvector**:
   ```bash
   # Start only the database service
   docker-compose up -d postgres
   ```

4. **Run the application**:
   ```bash
   cd app
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/images/upload` | Upload an image and generate embeddings |
| `GET` | `/api/v1/images/{image_id}` | Get image metadata |
| `GET` | `/api/v1/images/{image_id}/similar` | Find similar images |
| `GET` | `/api/v1/images/` | List all images (with pagination) |
| `DELETE` | `/api/v1/images/{image_id}` | Delete an image |

### Health Check Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health/` | Basic health check |
| `GET` | `/api/v1/health/detailed` | Detailed health information |
| `GET` | `/api/v1/health/ready` | Readiness probe |
| `GET` | `/api/v1/health/live` | Liveness probe |

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/image_processing` | Database connection URL |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_USER` | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL password |
| `POSTGRES_DB` | `image_processing` | PostgreSQL database name |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8080,http://localhost:8000` | Allowed CORS origins |
| `MAX_FILE_SIZE` | `10485760` | Maximum file size (10MB) |
| `ALLOWED_EXTENSIONS` | `.jpg,.jpeg,.png,.gif,.bmp` | Allowed file extensions |
| `EMBEDDING_DIMENSION` | `512` | Vector embedding dimension |
| `SIMILARITY_THRESHOLD` | `0.7` | Default similarity threshold |
| `MAX_SIMILAR_RESULTS` | `10` | Maximum similar results |

### Configuration File

Create a `.env` file in the project root or modify the existing one:

```bash
# Database configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/image_processing
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=image_processing

# Application settings
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
EMBEDDING_DIMENSION=512
SIMILARITY_THRESHOLD=0.7
```

## 🧪 Testing

### Run All Tests

```bash
# With Docker Compose (recommended)
docker-compose exec api pytest

# Local development
pytest
```

### Run Specific Test Categories

```bash
# API tests only
pytest tests/test_api/

# Service tests only
pytest tests/test_services/

# Specific test file
pytest tests/test_api/test_images.py

# With coverage
pytest --cov=app tests/
```

### Test Coverage

The test suite includes:

- **API Endpoint Tests**: All CRUD operations and error cases
- **Service Layer Tests**: Image processing and vector operations
- **Health Check Tests**: All health endpoints
- **Integration Tests**: End-to-end workflows
- **Mock Data**: Consistent test fixtures and sample images

## 📊 Usage Examples

### Upload an Image

```bash
curl -X POST "http://localhost:8000/api/v1/images/upload" \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@sample_image.jpg"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "sample_image.jpg",
  "message": "Image uploaded and processed successfully",
  "processing_status": "completed"
}
```

### Get Image Metadata

```bash
curl "http://localhost:8000/api/v1/images/550e8400-e29b-41d4-a716-446655440000"
```

### Find Similar Images

```bash
curl "http://localhost:8000/api/v1/images/550e8400-e29b-41d4-a716-446655440000/similar?limit=5&threshold=0.8"
```

Response:
```json
{
  "query_image_id": "550e8400-e29b-41d4-a716-446655440000",
  "similar_images": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "similar_image.jpg",
      "content_type": "image/jpeg",
      "similarity_score": 0.95,
      "upload_timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "total_results": 1,
  "search_timestamp": "2024-01-01T12:00:00Z"
}
```

## 🎨 Mock Embedding Generation

The service uses a sophisticated mock embedding system that:

1. **Generates consistent vectors** using hash-based seeding
2. **Produces normalized embeddings** suitable for cosine similarity
3. **Creates realistic similarity relationships** between images
4. **Uses configurable dimensions** (default: 512)

### How It Works

1. **Content Hashing**: Combines image content and filename hashes
2. **Reproducible Generation**: Same input always produces same embedding
3. **Vector Normalization**: All vectors are L2-normalized for cosine similarity
4. **Dimension Consistency**: All embeddings have exactly 512 dimensions

## 🗄️ Database Design

### Image Table Schema

```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    file_path VARCHAR(512),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_timestamp TIMESTAMP WITH TIME ZONE,
    embedding_vector VECTOR(512) NOT NULL,
    metadata JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending'
);

-- Index for similarity search
CREATE INDEX ON images USING ivfflat (embedding_vector vector_cosine_ops);
```

### pgvector Operations

- **Cosine Distance**: `embedding_vector <=> query_vector`
- **L2 Distance**: `embedding_vector <-> query_vector`
- **Inner Product**: `embedding_vector <#> query_vector`

## 🔍 Monitoring and Health Checks

### Health Check Endpoints

1. **Liveness** (`/api/v1/health/live`): Basic service availability
2. **Readiness** (`/api/v1/health/ready`): Service ready to handle requests
3. **Health** (`/api/v1/health/`): Comprehensive service and dependency status
4. **Detailed** (`/api/v1/health/detailed`): Full system information and statistics

### Monitoring Integration

The service provides structured health information suitable for:

- **Kubernetes probes**: Liveness and readiness endpoints
- **Load balancer health checks**: HTTP 200/503 responses
- **Monitoring systems**: Prometheus-compatible metrics
- **Alerting**: Detailed error information

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build the image
docker build -t image-processing-service .

# Run with external database
docker run -d \\
  --name image-processing-api \\
  -p 8000:8000 \\
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \\
  image-processing-service
```

### Docker Compose for Production

```yaml
version: '3.8'
services:
  api:
    image: image-processing-service:latest
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/production
      DEBUG: "false"
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Error: port is already allocated
   # Solution 1: Use different ports by editing docker-compose.yml
   # Change port mappings like "5433:5432" to "5434:5432"
   
   # Solution 2: Stop conflicting services
   sudo systemctl stop postgresql  # Stop system PostgreSQL
   docker-compose up -d
   
   # Solution 3: Check what's using the port
   sudo netstat -tulpn | grep :5433
   sudo lsof -i :5433
   ```

2. **Database Connection Failed**
   ```bash
   # Check PostgreSQL status
   docker-compose logs postgres
   
   # Verify pgvector extension
   docker-compose exec postgres psql -U postgres -d image_processing -c "SELECT * FROM pg_extension WHERE extname='vector';"
   ```

2. **Image Upload Fails**
   ```bash
   # Check file size limits
   curl -I http://localhost:8000/info
   
   # Verify allowed extensions
   grep ALLOWED_EXTENSIONS .env
   ```

3. **Similarity Search Returns No Results**
   ```bash
   # Check embedding statistics
   curl http://localhost:8000/api/v1/health/detailed
   
   # Verify similarity threshold
   curl "http://localhost:8000/api/v1/images/{id}/similar?threshold=0.1"
   ```

### Logs and Debugging

```bash
# View application logs
docker-compose logs api

# Enable debug mode
echo "DEBUG=true" >> .env
docker-compose restart api

# Database logs
docker-compose logs postgres
```

## 🤝 Contributing

1. **Code Style**: Follow PEP 8 and use type hints
2. **Testing**: Add tests for new features
3. **Documentation**: Update README and docstrings
4. **Commits**: Use conventional commit messages

### Development Workflow

```bash
# Install development dependencies
pip install -r requirements.txt

# Run linting
ruff check app/

# Run type checking
mypy app/

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Built with ❤️ for the Python Developer Technical Assessment**