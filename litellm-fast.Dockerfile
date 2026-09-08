FROM python:3.11-slim

WORKDIR /app

# Use Tsinghua mirror for MUCH faster downloads in China
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir 'litellm[proxy]' pyyaml

COPY litellm-config.yaml /app/config.yaml

EXPOSE 4000

CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0"]
