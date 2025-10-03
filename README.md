## Travel Assistant (FastAPI + React)

An AI-powered end-to-end travel planning app. Users can chat with an assistant to plan trips, automatically get itineraries with time budgets, hotel suggestions, and a transport plan between cities. The backend is built with FastAPI and MongoDB; the frontend is built with React + Material UI.

### Key Features
- Intelligent itinerary creation using multi-agent workflow (destination selection, routing, itinerary generation)
- Automatic transport plan (home → first city, inter-city, last city → home) with realistic durations and heuristic costs
- Hotel suggestions auto-generated in the background
- Real-time updates via WebSocket
- JWT authentication, protected routes, and CORS configuration
- Modern React UI with tabs: Chat, Itinerary, Hotels, Transport Plan

### Repository Structure (high level)
- `backend/app`: FastAPI application
  - `agents/`: Agents for routing, itinerary, detection/modification, workflow graph
  - `routers/`: API endpoints (`travels`, `auth`, `users`, etc.)
  - `services/`: Chat, hotel suggestions, daily visits, transport plan, AI matching
  - `core/`: Scheduler (time budgeting), prompt builder, auth/security helpers
  - `models/` and `crud/`: Pydantic models and MongoDB CRUD utilities
  - `config/`: Settings and tools config
- `frontend/`: React app (MUI-based) with `MainCanvas` and feature sections

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or remote)
- Azure OpenAI access (for itinerary generation and chat)

### Backend Setup
1) Create and activate a virtual environment, then install dependencies:
   - `cd backend`
   - `pip install -r requirements.txt`
   - Optional agents extras: `pip install -r requirements_agents.txt`

2) Create a `.env` file in `backend/app/config` root (or repo root if preferred) with at least:
   - `DEBUG=true`
   - `HOST=0.0.0.0`
   - `PORT=8000`
   - `MONGODB_URL=mongodb://localhost:27017`
   - `DATABASE_NAME=travel_app`
   - `SECRET_KEY=change_me`
   - `AZURE_OPENAI_API_KEY=...` (omit when MOCK_MODE=true)
   - `AZURE_OPENAI_ENDPOINT=...` (omit when MOCK_MODE=true)
   - `AZURE_OPENAI_API_VERSION=2024-02-15-preview` (example; omit when MOCK_MODE=true)
   - `AZURE_OPENAI_DEPLOYMENT_NAME=...` (omit when MOCK_MODE=true)
   - `MOCK_MODE=true` (to enable demo responses without external services)
   - `CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]`
   - Optional for realistic home flights:
     - `HOME_LAT=40.4168`
     - `HOME_LON=-3.7038`
   - Optional external keys:
     - `GOOGLE_MAPS_API_KEY=...`

3) Run the server:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - Or: `python -m app.main`

### Frontend Setup
1) `cd frontend`
2) `npm install`
3) Optional demo mode (no backend required):
   - Set `REACT_APP_MOCK=true` in your environment before starting the app
   - `REACT_APP_MOCK=true npm start`
   This enables a lightweight mock layer that simulates REST/WebSocket responses with demo data.

The app will open at `http://localhost:3000`. The backend defaults to `http://localhost:8000`.

---

## How It Works (Architecture)

### Backend (FastAPI + MongoDB)
- App initialization in `app/main.py`, CORS + security middlewares, routers included under `/api`
- MongoDB via Motor (async) with collections for travels, itineraries, messages, places, visits, flights, users, etc.
- Multi-agent orchestration:
  - `SmartItineraryWorkflow`: orchestrates itinerary detection/modification, database access, routing, and itinerary generation
  - `RoutingAgent`: builds a graph with geodesic distances, proposes route order (TSP approx, shortest path, proximity)
  - `ItineraryAgent`: asks Azure OpenAI to generate detailed itineraries from route & cities
  - `TimeBudgetScheduler`: allocates time across cities using a transport matrix and user’s total days
  - `TransportPlanService`: generates the “Transportes” plan automatically on itinerary create/update
- Background jobs: hotel suggestions and transport plan are scheduled automatically after itinerary changes
- WebSocket: `/api/travels/{travel_id}/ws` for real-time messages

### Frontend (React + MUI)
- Protected routes and modern UI in `MainCanvas`
- Tabs:
  - Chat: talk with the assistant
  - Itinerary: view itinerary and cities
  - Hotels: hotel suggestions
  - Transports: inter-city transport segments (including home legs)

---

## Configuration & Environment
The app reads environment variables in `backend/app/config/settings.py`. Notable settings:

- App & server: `HOST`, `PORT`, `DEBUG`
- Database: `MONGODB_URL`, `DATABASE_NAME`
- Azure OpenAI: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT_NAME`
- Demo: `MOCK_MODE` (backend) and `REACT_APP_MOCK` (frontend)
- CORS: `CORS_ORIGINS`
- Optional home coordinates for realistic home flights:
  - `HOME_LAT`, `HOME_LON`

If `HOME_LAT/HOME_LON` are set, the Transport Plan will calculate real distances and durations for the Home legs. If not set, the app uses conservative defaults (e.g., ~10h and a flat cost) to avoid underestimating long-haul flights.

When `MOCK_MODE=true` in the backend, the chat endpoints return predefined responses and chat history without hitting external services or Mongo writes. When `REACT_APP_MOCK=true` in the frontend, the app intercepts fetch/WebSocket calls to show a fully interactive demo with static data (suitable for GitHub Pages).

---

## API Overview

All endpoints are under `/api`. Auth is JWT-based (see `routers/auth.py`). Highlights from `routers/travel.py`:

- Travels
  - `GET /api/travels`: list travels
  - `POST /api/travels`: create a travel
  - `GET /api/travels/{travel_id}`: get a travel
  - `PUT /api/travels/{travel_id}`: update a travel
  - `DELETE /api/travels/{travel_id}`: delete a travel and related data

- Itinerary
  - `GET /api/travels/{travel_id}/itinerary`: get itinerary
  - `POST /api/travels/{travel_id}/itinerary`: create or update (1:1 per travel)

- Hotels
  - `GET /api/travels/{travel_id}/hotels/suggestions`: get hotel suggestions (generates if missing)

- Transport Plan (Transportes)
  - `GET /api/travels/{travel_id}/transport-plan`: returns the transport plan for the travel; generates it on-demand if absent

- WebSocket
  - `GET /api/travels/{travel_id}/ws?token=...`: bidirectional chat updates and processing

> Note: After creating/updating an itinerary, background tasks generate hotel suggestions and the transport plan automatically. You can also force generation by calling the corresponding GET endpoints.

---

## Transport Plan (Heuristics)
Implemented in `TransportPlanService` and `TravelTimeService`:

- Modes
  - Home → first city and last city → Home are always flights (configurable distance via `HOME_LAT/HOME_LON`)
  - Inter-city mode chosen by distance thresholds (heuristic):
    - < 80 km: private car
    - < 200 km: intercity bus
    - < 700 km: train
    - < 2000 km: flight (short/medium haul)
    - ≥ 2000 km: flight (long-haul)
  - If either city is recognized as an island (simple keyword heuristic) and distance < 300 km, the method is set to boat

- Durations
  - Derived from km/h per mode plus station/airport overheads
  - Flights differentiate domestic vs. international overheads

- Costs (heuristic)
  - Per-km cost per mode plus flat fees (flights have lower per-km but higher fixed fees)
  - Conservative defaults if home coordinates are not configured

These heuristics favor realism while remaining deterministic and fast (no external rate-limited services).

---

## Development Notes

### Tests
There are multiple test scripts under `backend/` and `backend/tests/`. You can run selected tests or integrate with `pytest` as needed.

### Troubleshooting
- 404 on `/transport-plan`: ensure the travel has an itinerary; if not, create/update it first. Verify `HOME_LAT/HOME_LON` if you expect realistic Home legs.
- Azure OpenAI errors: verify endpoint, deployment name, API version, and API key.
- CORS/auth errors: confirm `CORS_ORIGINS` and JWT token presence in requests.

### Docker (optional)
A `docker-compose.yml` is present. You can containerize the backend/frontend and a MongoDB instance with minor adjustments to env variables.

---

## License
Add your license here (e.g., MIT). 
