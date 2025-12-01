# Docker Deployment Guide

This guide explains how to deploy Bellweaver using Docker, which packages both the frontend and backend in a single container.

## Architecture

The Docker deployment uses a multi-stage build:

1. **Stage 1 (frontend-builder)**: Builds the React frontend using Node.js and Vite
2. **Stage 2 (backend)**: Installs Python dependencies and copies the built frontend into `bellweaver/static/`

The final container runs a Flask application that:
- Serves the React SPA from `/`
- Serves REST API endpoints from `/api/*`
- Handles client-side routing by serving `index.html` for non-API routes

## Prerequisites

- Docker (and Docker Compose recommended)
- Compass API credentials

## Quick Start with Docker Compose

### 1. Create environment file

Copy the example environment file and fill in your Compass credentials:

```bash
cp .env.docker.example .env
```

Edit `.env` with your credentials:

```bash
COMPASS_USERNAME=your_compass_username
COMPASS_PASSWORD=your_compass_password
COMPASS_BASE_URL=https://your-school.compass.education
```

### 2. Create data directory

```bash
mkdir -p data
```

This directory will persist your SQLite database outside the container.

### 3. Start the application

```bash
docker-compose up -d
```

This will:
- Build the Docker image (first time only)
- Start the container in detached mode
- Expose the application on port 5000

### 4. Access the application

Open your browser to:
- **Frontend**: http://localhost:5000
- **API**: http://localhost:5000/api/user or http://localhost:5000/api/events

### 5. Sync data from Compass

Before the dashboard will show data, you need to sync from Compass:

```bash
# Enter the running container
docker exec -it bellweaver bash

# Sync user details and calendar events
bellweaver compass sync

# Exit the container
exit
```

Or run as a one-liner:

```bash
docker exec -it bellweaver bellweaver compass sync
```

### 6. View logs

```bash
docker-compose logs -f
```

### 7. Stop the application

```bash
docker-compose down
```

To also remove the database volume:

```bash
docker-compose down -v
```

## Manual Docker Commands

If you prefer not to use Docker Compose:

### Build the image

```bash
docker build -t bellweaver:latest .
```

### Run the container

```bash
docker run -d \
  --name bellweaver \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e COMPASS_USERNAME=your_username \
  -e COMPASS_PASSWORD=your_password \
  -e COMPASS_BASE_URL=https://your-school.compass.education \
  bellweaver:latest
```

### View logs

```bash
docker logs -f bellweaver
```

### Stop the container

```bash
docker stop bellweaver
docker rm bellweaver
```

## API Routes

All API endpoints are prefixed with `/api`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/user` | GET | Get latest user details from Compass |
| `/api/events` | GET | Get calendar events from Compass |

## Troubleshooting

### Container fails health check

The health check tries to access `/api/user`. If it fails, check:

1. Database has been synced with Compass data:
   ```bash
   docker exec -it bellweaver bellweaver compass sync
   ```

2. Credentials are correct in `.env` file

3. Check logs for errors:
   ```bash
   docker-compose logs
   ```

### Frontend shows blank page

1. Check that the build completed successfully:
   ```bash
   docker logs bellweaver | grep "frontend"
   ```

2. Verify static files exist in the image:
   ```bash
   docker exec -it bellweaver ls -la /app/bellweaver/static
   ```

### API returns 404

Ensure you're using the `/api` prefix for all API calls:
- ✅ Correct: `http://localhost:5000/api/user`
- ❌ Incorrect: `http://localhost:5000/user`

### Database not persisting

Check that the data directory is mounted correctly:

```bash
docker inspect bellweaver | grep -A 10 Mounts
```

You should see `/app/data` mounted to your local `./data` directory.

## Production Considerations

### Security

1. **Never commit `.env` file** - it contains sensitive credentials
2. **Use secrets management** in production (e.g., Docker secrets, Kubernetes secrets)
3. **Enable HTTPS** using a reverse proxy (nginx, Traefik, Caddy)

### Scaling

This is a single-container deployment suitable for personal use. For production:

1. Use a reverse proxy (nginx/Traefie/Caddy) for HTTPS
2. Consider using a managed database instead of SQLite
3. Implement proper backup strategy for the database

### Updating

To update to a new version:

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build

# Restart container
docker-compose up -d
```

## Development vs Production

In development, you run frontend and backend separately:
- Frontend: `npm run dev` on port 3000 (with Vite proxy to backend)
- Backend: `poetry run bellweaver api serve` on port 5000

In production (Docker), both are served from a single container:
- Flask serves static frontend files from `/`
- Flask serves API from `/api/*`
- All traffic goes to port 5000
