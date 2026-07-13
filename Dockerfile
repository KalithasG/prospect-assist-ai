# Stage 1 — build the dashboard
FROM node:20-slim AS dashboard
WORKDIR /build
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 2 — serve API + dashboard from one FastAPI process
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY demo_server.py .
COPY --from=dashboard /build/dist dashboard/dist
ENV PORT=8000
EXPOSE 8000
CMD ["python", "demo_server.py"]
