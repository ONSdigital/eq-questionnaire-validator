FROM python:3.12-slim

RUN apt-get update && apt-get install --no-install-recommends -y git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install \
    setuptools \
    "poetry==1.8.3"
RUN poetry config virtualenvs.create false

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

COPY app /usr/src/app
COPY api.py poetry.lock pyproject.toml /usr/src/

RUN poetry install --only main

EXPOSE 5000

CMD ["gunicorn", "api:app", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "20", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "0"]
