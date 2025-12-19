FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    setuptools \
    "poetry==2.1.2"
RUN poetry config virtualenvs.create false

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

COPY app /usr/src/app
COPY api.py poetry.lock pyproject.toml /usr/src/

ENV AJV_VALIDATOR_SCHEME=http
ENV AJV_VALIDATOR_HOST=localhost
ENV AJV_VALIDATOR_PORT=5002

RUN poetry install --only main

# Create a non-root user and group
RUN adduser --group --system appuser

# Change ownership of the application directory to the non-root user
RUN chown -R appuser api.py poetry.lock pyproject.toml /usr/src/ app

# Set the user running the application to the non-root user
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5001/docs || exit 1

EXPOSE 5000

CMD ["gunicorn", "api:app", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "20", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--timeout", "0"]
