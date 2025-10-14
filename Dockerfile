FROM ghcr.io/astral-sh/uv:python3.13-bookworm
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync
COPY . .
CMD ["uv", "run", "main.py"]