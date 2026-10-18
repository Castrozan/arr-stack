FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/runtime:/app/runtime/arr_config_provisioner:/app/runtime/arr_users
WORKDIR /app
COPY runtime /app/runtime
COPY defaults /app/defaults
ENTRYPOINT ["python", "/app/runtime/main.py"]

FROM runtime AS tests
RUN pip install --no-cache-dir pytest==8.4.2
COPY tests /app/tests
COPY config /policy
ENTRYPOINT ["python", "-m", "pytest", "-q", "/app/tests"]

FROM runtime AS production
