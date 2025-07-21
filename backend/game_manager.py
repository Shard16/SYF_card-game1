# Game state, logic, turns, eliminations will be implemented here.

import random
from typing import Dict
from .models import GameState

from typing import Dict
from .models import GameState, Player, Card, CardType
from .card_effects import apply_card_effect


def build_full_deck():
    deck = []

    def add_cards(name, symbol, priority, count):
        for _ in range(count):
            deck.append(Card(name=name, symbol=symbol, priority=priority))

    # Based on card descriptions and expected frequency
    add_cards("Dagger", "🔪", 5, 8)
    add_cards("Shield", "🛡️", 3, 5)
    add_cards("Fireball", "🔥", 6, 4)
    add_cards("Bow", "🏹", 4, 4)
    add_cards("Love Potion", "💖", 2, 4)
    add_cards("Bomb", "💣", 7, 3)
    add_cards("Snake", "🐍", 8, 3)
    add_cards("Crystal", "🔮", 9, 3)
    add_cards("Goblin Hands", "👐", 1, 4)
    add_cards("Battle Axe", "🪓", 10, 4)
    add_cards("Left Potion", "🥤", 11, 2)
    add_cards("Golden Left Potion", "🥇", 0, 1)
    add_cards("Drink", "🍺", 12, 2)

    return deck


class GameManager:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
    
    deck = build_full_deck()
    random.shuffle(deck)

    def create_game(self, code: str, host_player: Player):
        # Initialize deck (for now, just a few cards for demo)
        deck =deck

        game = GameState(
            code=code,
            players=[host_player],
            deck=deck,
            discard=[],
            crown_index=0,
            phase="setup",
            round=1,
            played_cards={}  # player_id: {"card": Card, "target_id": str}
        )
        self.games[code] = game

    def get_game(self, code: str) -> GameState:
        return self.games.get(code)
    

    def join_game(self, code: str, player: Player):
        game = self.games.get(code)
        if not game:
            raise ValueError("Game not found")
        if any(p.username == player.username for p in game.players):
            raise ValueError("Username already taken in this game")
        if len(game.players) >= 5:  # Or use MAX_PLAYERS from config
            raise ValueError("Game is full")
        game.players.append(player)

    from .models import GameState, Player, Card

    def draw_cards(self, code: str, player_id: str):
        game = self.get_game(code)
        if not game:
            raise ValueError("Game not found")
        if game.phase != "draw":
            raise ValueError("Cannot draw cards outside of draw phase")
        player = next((p for p in game.players if p.id == player_id), None)
        if not player or player.eliminated:
            raise ValueError("Player not found or eliminated")
        # Enforce draw order: must be player's turn
        expected_player = game.players[(game.crown_index + len([p for p in game.players if len(p.hand) < 4])) % len(game.players)]
        if player != expected_player:
            raise ValueError("It's not your turn to draw")
        while len(player.hand) < 4 and game.deck:
            player.hand.append(game.deck.pop(0))


    def play_card(self, code: str, player_id: str, card_id: str, target_id: str):
        game = self.get_game(code)
        if not game:
            raise ValueError("Game not found")
        if game.phase != "play":
            raise ValueError("Cannot play cards outside of play phase")
        player = next((p for p in game.players if p.id == player_id), None)
        if not player or player.eliminated or player.snakebit or player.entranced:
            raise ValueError("Player cannot play this round")
        # Enforce play order: must be player's turn
        played_this_round = sum([len(plays) for plays in game.played_cards.values()])
        expected_player = game.players[(game.crown_index + played_this_round) % len(game.players)]
        if player != expected_player:
            raise ValueError("It's not your turn to play")
        card = next((c for c in player.hand if c.id == card_id), None)
        if not card:
            raise ValueError("Card not in hand")
        if player_id in game.played_cards and len(game.played_cards[player_id]) >= 2:
            raise ValueError("Player has already played two cards this round")
        player.hand = [c for c in player.hand if c.id != card_id]
        if player_id not in game.played_cards:
            game.played_cards[player_id] = []
        game.played_cards[player_id].append({"card": card, "target_id": target_id})


    def resolve_round(self, code: str):
        game = self.games.get(code)
        if not game:
            raise ValueError("Game not found")
        actions = []
        for player_id, plays in game.played_cards.items():
            for play in plays:
                actions.append({
                    "player_id": player_id,
                    "card": play["card"],
                    "target_id": play["target_id"]
                })
        def player_order(pid):
            idx = next((i for i, p in enumerate(game.players) if p.id == pid), None)
            if idx is None:
                return 999
            return (idx - game.crown_index) % len(game.players)
        actions.sort(key=lambda x: (x["card"].priority, player_order(x["player_id"])))
        # Apply effects and check elimination/victory after each
        for action in actions:
            apply_card_effect(game, action)
            game.discard.append(action["card"])
            # Eliminate players with 0 or less health immediately
            for player in game.players:
                if player.health <= 0 and not player.eliminated:
                    player.eliminated = True
            # Check win condition immediately
            alive_players = [p for p in game.players if not p.eliminated]
            if len(alive_players) == 1:
                game.phase = "end"
                game.winner = alive_players[0].username
                game.played_cards = {}
                return  # End round immediately if only one remains
        # If more than one player remains, advance as usual
        game.phase = "draw"
        game.round += 1
        game.played_cards = {}
    
    def next_round(self, code: str):
        game = self.games.get(code)
        if not game:
            raise ValueError("Game not found")
        # Rotate crown to the left (next player who is not eliminated)
        alive_players = [p for p in game.players if not p.eliminated]
        if not alive_players:
            game.phase = "end"
            return
        # Find next alive player
        next_crown = (game.crown_index + 1) % len(game.players)
        while game.players[next_crown].eliminated:
            next_crown = (next_crown + 1) % len(game.players)
        game.crown_index = next_crown
        for idx, player in enumerate(game.players):
            player.is_royal = (idx == game.crown_index)
        # Reset per-round statuses
        for player in game.players:
            player.shield = 0
            if player.snakebit:
                player.snakebit = False
            if player.entranced:
                player.entranced = False
        # Handle bombs: deal damage if primed
        for player in game.players:
            for card in list(player.hand):
                if getattr(card, "is_primed", False):
                    player.health -= 1
                    player.hand.remove(card)
                    game.discard.append(card)
        # Advance round number and phase
        game.round += 1
        game.phase = "draw"
        # Draw up to 4 cards for each alive player, starting with royal highness
        start = game.crown_index
        for i in range(len(game.players)):
            idx = (start + i) % len(game.players)
            player = game.players[idx]
            if player.eliminated:
                continue
            while len(player.hand) < 4 and game.deck:
                player.hand.append(game.deck.pop(0))

                # If deck is empty, reshuffle discard into deck
                if not game.deck:
                    game.deck = game.discard
                    game.discard = []
                    random.shuffle(game.deck)
game_manager = GameManager()