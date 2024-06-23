# Use a multi-stage build to minimize the final image size
# Stage 1: Build stage
FROM python:3.12-alpine AS build

# Setup environment variable
ENV DockerHOME=/home/app/webapp

# Set environment variables to avoid writing .pyc files and enable buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1  

# Install build dependencies
RUN apk update && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    cargo \
    && pip install --upgrade pip \
    && pip install \
    celery \
    flower \
    django \
    django-environ \
    python-decouple \
    dj_database_url \
    django-crispy-forms \
    crispy-bootstrap5 \
    django_extensions \
    psycopg2-binary \
    ChatbotAPI \
    whitenoise \
    redis[hiredis] \
    django-redis \
    gunicorn \
    pytube \
    lyrics_extractor \
    youtube_search \
    pillow \
    django-sesame \
    google-api-python-client \
    pandas \
    django-recaptcha \
    && apk del .build-deps

# Stage 2: Production stage
FROM python:3.12-alpine

# Setup environment variable
ENV DockerHOME=/home/app/webapp

# Set work directory
WORKDIR $DockerHOME

# Copy dependencies from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy the whole project to your docker home directory
COPY . $DockerHOME
