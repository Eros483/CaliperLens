FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY backend/pyproject.toml backend/.python-version* ./
RUN uv sync --frozen 2>/dev/null || uv sync

COPY backend/ ./backend/
COPY dbt/ ./dbt/
COPY sandbox/ ./sandbox/

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
