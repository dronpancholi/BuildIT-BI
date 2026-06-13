# Healthcare Financial Intelligence Platform

An AI-Native Healthcare Financial Intelligence Platform that transforms healthcare financial data into actionable insights, predictions, and recommendations.

## Features

- **Executive Command Center**: Real-time KPI monitoring with AI-powered insights
- **Revenue Intelligence**: Deep analysis of revenue streams and trends
- **AI Insights Engine**: Automatic anomaly detection, trend analysis, and opportunity identification
- **AI CFO Assistant**: Natural language interface for financial queries
- **Forecasting Platform**: AI-powered forecasting with confidence intervals
- **Scenario Lab**: Financial simulation and scenario modeling
- **Alert Center**: Intelligent alert management and notifications

## Tech Stack

### Frontend
- Next.js 15 with TypeScript
- Tailwind CSS
- shadcn/ui components
- ECharts for visualizations
- Zustand for state management

### Backend
- FastAPI (Python)
- SQLAlchemy (Async)
- PostgreSQL
- Redis (Caching)
- Celery (Background jobs)

### AI/ML
- Nvidia NIM API
- Scikit-learn
- Statsmodels
- Polars/Pandas

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthcare-fi-platform
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Start the databases**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

6. **Start the development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

7. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

### Using Docker Compose

```bash
docker-compose up -d
```

This will start all services including PostgreSQL, Redis, Backend, and Frontend.

## Project Structure

```
healthcare-fi-platform/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities, API client, types
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Configuration, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   └── requirements.txt
├── infrastructure/          # Docker, deployment configs
└── docker-compose.yml
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### KPIs
- `GET /api/v1/kpis/executive-summary` - Executive summary
- `GET /api/v1/kpis/revenue` - Revenue KPIs
- `GET /api/v1/kpis/profitability` - Profitability KPIs
- `GET /api/v1/kpis/occupancy` - Occupancy KPIs
- `GET /api/v1/kpis/claims` - Claims KPIs

### Insights
- `GET /api/v1/insights/comprehensive` - Comprehensive insights
- `GET /api/v1/insights/anomalies` - Detect anomalies
- `GET /api/v1/insights/trends` - Analyze trends
- `GET /api/v1/insights/opportunities` - Identify opportunities

### Forecasts
- `POST /api/v1/forecasts/create` - Generate forecast
- `GET /api/v1/forecasts/historical/{metric_type}` - Get historical data

### Scenarios
- `POST /api/v1/scenarios/simulate` - Run simulation
- `POST /api/v1/scenarios/save` - Save scenario

### Alerts
- `GET /api/v1/alerts/list` - List alerts
- `PUT /api/v1/alerts/{id}/read` - Mark as read
- `PUT /api/v1/alerts/{id}/resolve` - Resolve alert

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `NVIDIA_NIM_API_KEY` - Nvidia NIM API key
- `ENVIRONMENT` - Environment (development/production)
- `DEBUG` - Enable debug mode

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL

## License

Proprietary - All rights reserved
