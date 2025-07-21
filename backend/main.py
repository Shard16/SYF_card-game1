from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters


from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from backend.models import Player
from backend.game_manager import game_manager
from fastapi import BackgroundTasks
import json
from typing import Dict, List
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
import os



active_connections: Dict[str, List[WebSocket]] = {}

async def broadcast_game_state(game_code: str, game_state):
    if game_code in active_connections:
        data = json.dumps(game_state.dict())
        for ws in active_connections[game_code]:
            try:
                await ws.send_text(data)
            except Exception:
                pass  # Ignore failed sends



app = FastAPI(
    title="Stab Your Friends API",
    description="Backend for the Stab Your Friends Telegram WebApp",
    version="0.1.0"
)


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Allow frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fc8343d703b2.ngrok-free.app"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Stab Your Friends backend is running!"}


@app.post("/create_game")
async def create_game(username: str, background_tasks: BackgroundTasks = None):  # MODIFIED: add background_tasks
    # Generate a unique game code (e.g., 6 uppercase letters)
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase, k=6))
    host_player = Player(id=code + "_host", username=username)
    game_manager.create_game(code, host_player)
    game = game_manager.get_game(code)
    if background_tasks:
        background_tasks.add_task(broadcast_game_state, code, game)
    return {"game_code": code}

@app.post("/join_game")
async def join_game(
    game_code: str = Body(...),
    username: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    from models import Player
    player = Player(id=game_code + "_" + username, username=username)
    try:
        game_manager.join_game(game_code, player)
        game = game_manager.get_game(game_code)
        if background_tasks:
            background_tasks.add_task(broadcast_game_state, game_code, game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"{username} joined game {game_code}"}

@app.get("/players/{game_code}")
async def get_players(game_code: str):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return [player.dict() for player in game.players]

# ...existing code...

@app.post("/draw")
async def draw(
    game_code: str = Body(...),
    player_id: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.phase != "draw":
        raise HTTPException(status_code=400, detail="Not in draw phase")
    try:
        game_manager.draw_cards(game_code, player_id)
        if background_tasks:
            background_tasks.add_task(broadcast_game_state, game_code, game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Cards drawn", "hand": [card.dict() for card in next(p for p in game.players if p.id == player_id).hand]}


@app.post("/play_card")
async def play_card_endpoint(
    game_code: str = Body(...),
    player_id: str = Body(...),
    card_id: str = Body(...),
    target_id: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.phase != "play":
        raise HTTPException(status_code=400, detail="Not in play phase")
    try:
        game_manager.play_card(game_code, player_id, card_id, target_id)
        if background_tasks:
            background_tasks.add_task(broadcast_game_state, game_code, game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Card played"}


@app.post("/resolve_round")
async def resolve_round(
    game_code: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.phase != "resolve":
        raise HTTPException(status_code=400, detail="Not in resolve phase")
    try:
        game_manager.resolve_round(game_code)
        if background_tasks:
            background_tasks.add_task(broadcast_game_state, game_code, game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Round resolved"}

@app.post("/next_round")
async def next_round(
    game_code: str = Body(...),
    background_tasks: BackgroundTasks = None
):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.phase != "draw":  # Only allow next round from draw phase
        raise HTTPException(status_code=400, detail="Not ready for next round")
    try:
        game_manager.next_round(game_code)
        if background_tasks:
            background_tasks.add_task(broadcast_game_state, game_code, game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Next round started"}



@app.get("/game_state/{game_code}")
async def game_state(game_code: str):
    game = game_manager.get_game(game_code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.websocket("/ws/{game_code}")
async def websocket_endpoint(websocket: WebSocket, game_code: str):
    await websocket.accept()
    if game_code not in active_connections:
        active_connections[game_code] = []
    active_connections[game_code].append(websocket)
    try:
        while True:
            # Wait for any message from client (could be a ping or action)
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[game_code].remove(websocket)

# BOT_TOKEN = os.getenv("8068386210:AAEiyCP3-0PVksVkX8fgomIj5JiwVuAqAbY")  # Or paste your token directly for local dev
# WEBAPP_URL = "https://fc8343d703b2.ngrok-free.app/menu.html"  # <-- Replace with your deployed frontend URL

# async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [
#         [InlineKeyboardButton("▶️ Play Stab Your Friends", web_app=WebAppInfo(url=WEBAPP_URL))]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text(
#         "Welcome to Stab Your Friends!\nTap below to start the game.",
#         reply_markup=reply_markup
#     )

# def run_telegram_bot():
#     app = ApplicationBuilder().token(BOT_TOKEN).build()
#     app.add_handler(CommandHandler("start", start_command))
#     # Add more bot handlers if needed
#     app.run_polling()

# if __name__ == "__main__":
#     import threading
#     threading.Thread(target=run_telegram_bot, daemon=True).start()
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)