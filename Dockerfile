FROM python:3.6-alpine

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
