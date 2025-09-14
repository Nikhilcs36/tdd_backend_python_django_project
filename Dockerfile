FROM python:3.9-alpine3.13
LABEL maintainer="nikhilcs36"

# Prevent Python from buffering stdout/stderr (for better logging)
ENV PYTHONUNBUFFERED=1

# Copy dependency files and source code
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# Optional: enable extra packages in dev mode
ARG DEV=false

# Set up Python venv, install dependencies, and prepare environment
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    \
    # Install MySQL client library (runtime only)
    apk add --no-cache mariadb-connector-c && \
    \
    # Install build dependencies for mysqlclient (temporary)
    apk add --no-cache --virtual .tmp-build-deps \
        build-base \
        mariadb-dev \
        musl-dev && \
    \
    # Install Python dependencies
    /py/bin/pip install -r /tmp/requirements.txt && \
    \
    # Optionally install dev dependencies if DEV=true
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    \
    # Clean up build packages and temp files
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    \
    # Add a non-root user for security
    adduser --disabled-password --no-create-home django-user && \
    \
    # Create media directory and change ownership
    RUN mkdir -p /app/media && \
        chown -R django-user:django-user /app/media

# Set default Python path to virtual environment
ENV PATH="/py/bin:$PATH"

# Use non-root user to run the app
USER django-user
