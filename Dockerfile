FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN addgroup --system dera && adduser --system --ingroup dera --home /nonexistent --no-create-home dera
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir -e . \
    && mkdir -p /data /tmp/dera \
    && chown -R dera:dera /data /tmp/dera /app

USER dera
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
