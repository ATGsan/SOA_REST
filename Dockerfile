FROM python:3.8-slim

WORKDIR .
COPY main.py .

RUN pip install fastapi[all] uvicorn pika

RUN uvicorn main:app --reload
