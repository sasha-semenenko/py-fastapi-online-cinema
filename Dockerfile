FROM python:3.10

# Setting environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installing dependencies
RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    && apt clean

# Install Poetry
RUN python -m pip install --upgrade pip && \
    pip install poetry

# Selecting a working directory
WORKDIR /app

# Copy the source code
COPY ./src .
