FROM python:3.11-slim
RUN pip install --no-cache-dir 'litellm[proxy]' prisma pyyaml
COPY litellm-config.yaml /app/config.yaml
EXPOSE 4000
CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000", "--num_workers", "4"]
