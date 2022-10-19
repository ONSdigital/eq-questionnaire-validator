FROM python:3.10-slim

RUN apt-get update && apt-get install --no-install-recommends -y git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==1.2.1"
RUN poetry config virtualenvs.create false

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

COPY app /usr/src/app
COPY api.py poetry.lock pyproject.toml /usr/src/

RUN poetry install --no-dev

EXPOSE 5000

ENV FLASK_APP=api.py

ENTRYPOINT flask run --host 0.0.0.0

