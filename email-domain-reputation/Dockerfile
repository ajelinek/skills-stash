FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir requests==2.32.3

COPY scripts/check_reputation.py /app/check_reputation.py

ENTRYPOINT ["python3", "/app/check_reputation.py"]
