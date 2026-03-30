# /home/mohith/Catchup-Mohith/backend/Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev netcat-openbsd redis-tools curl \
    && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos "" appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 \
     /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
RUN chmod +x wait-for-services.sh
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["./wait-for-services.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", \
     "--port", "8000"]
