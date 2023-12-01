FROM python:3.11.6-slim

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh
