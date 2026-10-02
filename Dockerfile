FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY data/sample ./data/sample
RUN pip install --no-cache-dir .
ENTRYPOINT ["medallion"]
CMD ["run", "--source", "sample", "--config", "config/local.json"]
