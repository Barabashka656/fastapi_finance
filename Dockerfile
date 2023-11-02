FROM python:3.11.6-slim

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

RUN chmod a+x docker/*.sh

RUN mkdir -p /fastapi_app/migrations/versions

CMD gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000

