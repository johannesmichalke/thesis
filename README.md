# How to Run This Project

This project consists of a Python FastAPI backend and a JavaScript frontend (e.g., built with React or Next.js).

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install uvicorn

uvicorn main:app --host 0.0.0.0 --port 8000
```
