# Sentralert Demo Service

A demo FastAPI application showcasing e-commerce endpoints with Sentry integration, deployable to Render with zero configuration.

## Features

- Product catalog and detail endpoints
- Checkout flow with configurable modes (normal, slow, error)
- Order creation and refund processing
- Inventory management
- ML-based recommendations
- Sentry error tracking and performance monitoring
- Test scenario endpoints for load testing

## Local Development

### Prerequisites

- Python 3.9+
- UV or pip for package management

### Setup

1. Install dependencies:
```bash
uv sync
# or
pip install -e .
```

2. Create a `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
```

3. Run the development server:
```bash
uvicorn sentralert_demo_service.app:app --reload
```

The API will be available at `http://localhost:8000`

## Render Deployment

This application is configured to deploy to Render with zero configuration using the included [render.yaml](render.yaml) file.

### Prerequisites

- GitHub account (Render deploys from Git repositories)
- Render account (free tier available at [render.com](https://render.com))

### Deployment Methods

#### Option 1: Deploy via Render Dashboard

1. **Push your code to GitHub** (if not already there)

2. **Create a new Web Service on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Set environment variables** in the Render Dashboard:
   - `SENTRY_DSN` - Your Sentry DSN for error tracking
   - `SCENARIO_BASE_URL` - Your Render app URL (e.g., `https://sentralert-demo-service.onrender.com`)

4. **Deploy!** Render will automatically build and deploy your app

#### Option 2: One-Click Deploy

Click the button below to deploy directly to Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

#### Option 3: Using Render Blueprint

If you have the Render CLI installed:

```bash
# Install Render CLI
brew install render  # macOS
# or download from https://render.com/docs/cli

# Deploy using the render.yaml blueprint
render blueprint launch
```

### Configuration

The Render configuration is in [render.yaml](render.yaml):

- **Service type:** Web Service
- **Runtime:** Python 3.11
- **Plan:** Free tier (512MB RAM, shared CPU)
- **Region:** Oregon (configurable)
- **Auto-deploy:** Enabled on git push
- **Health check:** `/health` endpoint

### Environment Variables

Set these in the Render Dashboard under "Environment":

- `SENTRY_DSN` - Your Sentry DSN for error tracking (optional)
- `SCENARIO_BASE_URL` - Base URL for scenario endpoints (your Render URL)
- `ENVIRONMENT` - Deployment environment (default: "production")
- `RELEASE` - Release version (default: "v1.0.0")

### Free Tier Limitations

- **Spin down:** Service spins down after 15 minutes of inactivity
- **Cold starts:** First request after spin down takes ~30-60 seconds
- **RAM:** 512MB
- **CPU:** Shared CPU (0.1 CPU)
- **Hours:** 750 hours/month (sufficient for 24/7 uptime)

**Tip:** To keep the service warm, set up a free uptime monitoring service (like UptimeRobot) to ping your `/health` endpoint every 10 minutes.

### Custom Domain

To use a custom domain:

1. Go to your service in Render Dashboard
2. Click "Settings" → "Custom Domain"
3. Add your domain and follow DNS instructions

### Monitoring & Logs

- **Render Dashboard:** View logs, metrics, and events at [dashboard.render.com](https://dashboard.render.com)
- **Sentry:** Error tracking and performance monitoring
- **Live logs:** Click "Logs" in the Render Dashboard for real-time log streaming

### Deployment Info

After deployment, your app will be available at:
```
https://sentralert-demo-service.onrender.com
```

**Note:** The URL will be different based on your service name.

## API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /catalog` - Product catalog
- `GET /product/{product_id}` - Product details
- `GET /checkout` - Checkout flow (supports `mode` parameter: normal, slow, error)

### API Endpoints

- `POST /api/orders` - Create order
- `GET /api/inventory/{sku}` - Check inventory
- `POST /api/refunds` - Process refund
- `GET /api/recommendations/{user_id}` - Get ML recommendations
- `DELETE /api/cache/clear` - Clear cache (admin)

### Test Scenario Endpoints

- `POST /scenario/baseline` - Generate baseline traffic
- `POST /scenario/checkout-error-spike` - Trigger checkout errors
- `POST /scenario/checkout-latency-spike` - Trigger checkout latency
- `POST /scenario/trigger-orders` - Trigger order creation with errors
- `POST /scenario/inventory-timeouts` - Trigger inventory timeouts

## License

MIT
