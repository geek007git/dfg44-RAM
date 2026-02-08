# Job Commission Platform

This is a premium Job Commission platform built with FastAPI and SQLite.

## Start the Server

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Seed the database (optional, already done):
   ```bash
   python -m backend.seed
   ```

3. Run the development server:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. Open your browser at `http://localhost:8000`.

## Features

- **FastAPI Backend**: fast, async, and robust.
- **SQLite Database**: embedded, serverless database.
- **Premium UI**: Custom dark theme with glassmorphism effects.
- **Responsive Design**: works on all devices.
