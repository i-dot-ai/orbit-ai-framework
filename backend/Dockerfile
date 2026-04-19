FROM public.ecr.aws/docker/library/python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml uv.lock ./

# Copy minimal structure needed for installation
COPY backend backend
COPY shared_utils shared_utils

# Install project dependencies using uv
RUN uv sync --locked --no-dev --extra fastapi

COPY alembic.ini alembic.ini
COPY alembic alembic


# Expose the port the app runs on
EXPOSE 8080

HEALTHCHECK CMD curl --fail http://localhost:8080/api/healthcheck

# Command to run the FastAPI app using Uvicorn
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
