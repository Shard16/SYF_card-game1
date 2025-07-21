# Stab Your Friends (Telegram Card Game)

A Telegram-based multiplayer card game built with FastAPI (backend) and HTML/JS (frontend).

## Structure

See `Game rules.txt` and project folders for details.

# Stab Your Friends

A Telegram WebApp card game built with FastAPI (backend) and HTML/JS (frontend).

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the backend:
   ```
   uvicorn backend.main:app --reload
   ```

3. Open `frontend/game.html` in your browser (or via Telegram WebApp).

## Project Structure

- `backend/` - FastAPI backend
- `frontend/` - Web frontend
- `shared/` - Shared config/constants