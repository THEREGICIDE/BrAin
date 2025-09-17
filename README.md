# AI Trip Planner

Minimal scaffold for a FastAPI backend and Streamlit frontend.

## Run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```
Open http://localhost:9000/docs

## Run frontend
```bash
cd frontend
pip install -r requirements.txt
# Ensure API_BASE is set (or edit frontend/.env)
export API_BASE=http://localhost:9000
streamlit run app.py --server.port 8502
```
Open http://localhost:8502

## Notes
- `/api/trips/plan` — plan a trip from origin to destination (mock logic).
- `/api/chat` — simple chat endpoint.
- `/api/payments/intent` — mock payment intent.
