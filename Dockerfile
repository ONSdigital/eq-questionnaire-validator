FROM python:3.8-slim

RUN apt-get update && apt-get install --no-install-recommends -y git=1:2.20.1-2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv==2018.11.26

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

EXPOSE 5000

ENV FLASK_APP=api.py

ENTRYPOINT flask run --host 0.0.0.0

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --system

COPY . /usr/src/app
