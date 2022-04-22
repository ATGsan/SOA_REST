FROM python:3.8-slim

WORKDIR .
COPY main.py .

ENTRYPOINT ["python", "main.py"]
