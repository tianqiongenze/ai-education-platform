FROM m.daocloud.io/docker.io/library/python:3.11-slim

WORKDIR /app

# Use Tsinghua mirror for fast, reliable downloads in China
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir 'litellm[proxy]' prisma pyyaml && \
    pip cache purge

EXPOSE 4000

CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0", "--num_workers", "1"]
