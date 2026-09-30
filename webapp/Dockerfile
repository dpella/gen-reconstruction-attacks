# Showcase web app. Build from the repository root:
#   docker build -f webapp/Dockerfile -t reconstruction-showcase .
#   docker run --rm -p 8000:8000 reconstruction-showcase

# --- Frontend: Vite + React -> static files --------------------------------
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY webapp/frontend/package.json webapp/frontend/package-lock.json ./
RUN npm ci
COPY webapp/frontend/ ./
RUN npm run build

# --- Backend: the generator + FastAPI --------------------------------------
FROM python:3.11.9-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends glpk-utils build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY webapp/backend/requirements.txt webapp/backend/requirements.txt
RUN pip install --no-cache-dir -r webapp/backend/requirements.txt

COPY src/ src/
COPY experiments/common/driver.py experiments/common/driver.py
COPY webapp/backend/ webapp/backend/

# Every dataset the site serves is deterministic, so generate them all now
# (~5 min); the running container never invokes the solver.
ENV CACHE_DIR=/app/webapp/cache
RUN python -m webapp.backend.engine
# Fail the build if any published query disagrees with its dataset.
COPY webapp/check_datasets.py webapp/check_datasets.py
RUN python webapp/check_datasets.py

COPY --from=frontend /frontend/dist webapp/frontend/dist

RUN useradd --system --uid 10001 app && chown -R app /app/webapp/cache
USER app
EXPOSE 8000
CMD ["uvicorn", "webapp.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
