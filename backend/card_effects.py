def choose_bounce_target(game, exclude):
    # simplest: next alive clockwise that’s not in exclude
    players = game.players
    start_idx = next(i for i, p in enumerate(players) if p.id == exclude[0])
    for i in range(1, len(players)):
        idx = (start_idx + i) % len(players)
        if players[idx].id not in exclude and not players[idx].eliminated:
            return players[idx]
    return None

def is_blocked_by_shield(card_type, target):
    return card_type != "Battle Axe" and hasattr(target, "shield") and target.shield > 0



def apply_card_effect(game, action):
    card_type = action["card"].type
    target = next((p for p in game.players if p.id == action["target_id"]), None)
    player = next((p for p in game.players if p.id == action["player_id"]), None)

    if not target or target.eliminated:
        return

    # Dagger: Target loses 1 health
    if card_type == "Dagger":
        if is_blocked_by_shield(card_type, target):
            target.shield -= 1
            return
        target.health -= 1


    # Shield: Target gains a shield (implement as a boolean or counter)
    elif card_type == "Shield":
        if not hasattr(target, "shield"):
            target.shield = 0
        target.shield += 1

    # Bow: Target loses 1 health
    elif card_type == "Bow":
        if is_blocked_by_shield(card_type, target):
            target.shield -= 1
            return
        target.health -= 1

    elif card_type == "Bomb":
        action["card"].primed = True  # Mark the bomb card as primed
        action["card"].persistent = True  # Optional: flag it stays in play


    # Fireball: Target loses 2 health

    elif card_type == "Fireball":
        if target and not target.eliminated:
            target.health -= 1
            if target.health <= 0:
                target.eliminated = True      # or add to eliminated_ids list
            else:
                # choose another player (you can prompt in UI or pick clockwise)
                bounce_target = choose_bounce_target(game, exclude=[target.id])
                if bounce_target:
                    bounce_target.health -= 1
                    if bounce_target.health <= 0:
                        bounce_target.eliminated = True


    # Love Potion: Target is entranced (skip next turn, for example)
    elif card_type == "Love Potion":
        target.entranced = True

    # Snake: Target is snakebit (implement snakebit logic)
    elif card_type == "Snake":
        target.snakebit = True

    # Crystal: Target draws 1 card (if deck not empty)
    elif card_type == "Crystal":
        if game.deck:
            target.hand.append(game.deck.pop(0))

    # Drink: Target regains 1 health (up to max)
    elif card_type == "Drink":
        if target.health < 5:
            target.health += 1

    # Golden Left Potion: Target swaps hands with player to their left
    elif card_type == "Golden Left Potion":
        idx = game.players.index(target)
        left_idx = (idx + 1) % len(game.players)
        left_player = game.players[left_idx]
        target.hand, left_player.hand = left_player.hand, target.hand

    # Left Potion: Target passes a card to player on their left
    elif card_type == "Left Potion":
        idx = game.players.index(target)
        left_idx = (idx + 1) % len(game.players)
        left_player = game.players[left_idx]
        if target.hand:
            left_player.hand.append(target.hand.pop(0))

    # Goblin Hands: Target discards a random card (if any)
    elif card_type == "Goblin Hands":
        import random
        if target.hand:
            discarded = target.hand.pop(random.randrange(len(target.hand)))
            game.discard.append(discarded)

    # Battle Axe: Target loses 2 health
    elif card_type == "Battle Axe":
        if hasattr(target, "shield") and target.shield > 0:
            target.health -= 2
            target.shield -= 1
        # If no shield, Battle Axe does nothing

    # Add more card effects as needed

    # Handle shield logic: If target has shield, block one damage and reduce shield
    if hasattr(target, "shield") and target.shield > 0 and card_type in ["Dagger", "Bow", "Fireball", "Battle Axe"]:
        # Block the damage, restore health, and reduce shield
        if card_type == "Dagger":
            target.health += 1
        elif card_type == "Bow":
            target.health += 1
        elif card_type == "Fireball":
            target.health += 2
        elif card_type == "Battle Axe":
            target.health += 2
        target.shield -= 1