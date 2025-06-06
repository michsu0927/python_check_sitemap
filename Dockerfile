# syntax=docker/dockerfile:1

# Builder stage to install dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /install /usr/local
COPY . .
# create non-root user
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app
CMD ["python", "src/main.py", "--help"]
