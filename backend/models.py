# Pydantic models for requests and responses will be defined here.
from typing import List, Optional, Dict
from pydantic import BaseModel
import enum


class CardType(str, enum.Enum):
    GOLDEN_LEFT_POTION = "Golden Left Potion"
    LEFT_POTION = "Left Potion"
    GOBLIN_HANDS = "Goblin Hands"
    SHIELD = "Shield"
    BATTLE_AXE = "Battle Axe"
    BOW = "Bow"
    FIREBALL = "Fireball"
    DAGGER = "Dagger"
    BOMB = "Bomb"
    LOVE_POTION = "Love Potion"
    SNAKE = "Snake"
    CRYSTAL = "Crystal"
    DRINK = "Drink"

class Card(BaseModel):
    id: str
    type: CardType
    priority: int
    description: str
    is_primed: bool = False  # For bombs, snakes, etc.

class Player(BaseModel):
    id: str
    username: str
    health: int = 5
    hand: List[Card] = []
    is_royal: bool = False
    eliminated: bool = False
    snakebit: bool = False
    entranced: bool = False
    is_primed: bool = False
    shield: int = 0

class GameState(BaseModel):
    code: str
    players: List[Player]
    deck: List[Card]
    discard: List[Card]
    crown_index: int = 0
    phase: str = "setup"  # setup, draw, play, resolve, end
    round: int = 1
    played_cards: Dict[str, Dict] = {}
    winner: Optional[str] = None  
    current_turn_player_id: str 
