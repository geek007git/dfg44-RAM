# Job Commission Platform

This is a premium Job Commission platform built with FastAPI. It uses **SQLite** for local development and **PostgreSQL** (e.g., Supabase, Neon) for production deployments on Vercel.

## Quick Start (Local Development)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Seed the database** (optional, for initial data):
   ```bash
   python -m backend.seed
   ```

3. **Run the development server**:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. Open your browser at `http://localhost:8000`.

## Deployment on Vercel

This project is configured for easy deployment on [Vercel](https://vercel.com/) with a Python runtime.

1. **Import Project**: Import this repository into Vercel.
2. **Environment Variables**: You **MUST** set the `DATABASE_URL` environment variable for the production database.
   - For **Supabase/Postgres**: Use your connection string (e.g., `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`).
   - *Note: The app automatically handles `postgres://` to `postgresql://` conversion.*
3. **Deploy**: Click deploy. The `vercel.json` is pre-configured to handle the Python backend and static frontend assets.

## Features

- **FastAPI Backend**: Fast, async, and robust API.
- **Dual Database Support**: 
  - **SQLite** for zero-config local development.
  - **PostgreSQL** for scalable production environments.
- **Premium UI**: Custom dark theme with glassmorphism effects.
- **Responsive Design**: Fully responsive across mobile and desktop.
