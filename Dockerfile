FROM python:3.11-slim

RUN apt-get update && apt-get install --no-install-recommends -y git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==1.3.2"
RUN poetry config virtualenvs.create false

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

COPY app /usr/src/app
COPY api.py poetry.lock pyproject.toml /usr/src/

RUN poetry install --no-dev

EXPOSE 5000

#ENTRYPOINT ["fastapi", "run", "api.py", "--host", "0.0.0.0"]
CMD ["gunicorn", "api:app", "-b", "0.0.0.0:5000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--timeout", "0"]
