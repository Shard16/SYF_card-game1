// JS logic for drag, draw, play, WebSocket, etc. will go here.

// scripts/game.js

const API_BASE = "https://fc8343d703b2.ngrok-free.app"; // Adjust if needed
const gameCode = localStorage.getItem("game_code");
const username = localStorage.getItem("username");
const playerId = `${gameCode}_${username}`;
const bottomHand = document.getElementById("bottomHand");
const gameArea = document.getElementById("gameArea");
let ws;

// Connect to WebSocket for live game state updates
function connectWebSocket() {
    if (!gameCode) return;
    ws = new WebSocket(`${API_BASE.replace(/^http/, "ws")}/ws/${gameCode}`);
    ws.onmessage = (event) => {
        const state = JSON.parse(event.data);
        renderGame(state);
    };
    ws.onclose = () => setTimeout(connectWebSocket, 2000);
}
connectWebSocket();

async function fetchGameState() {
    try {
        const res = await fetch(`${API_BASE}/game_state/${gameCode}`);
        const data = await res.json();
        renderGame(data);
    } catch (err) {
        console.error("Failed to fetch game state:", err);
    }
}

let currentGameState = null;


function renderGame(state) {
    currentGameState = state; // Store the current state for later use
    const isMyTurn = state.current_turn_player_id === playerId;
    const isPlayPhase = state.phase === "play";
    const isDrawPhase = state.phase === "draw";

    document.getElementById("phaseIndicator").innerText = `Phase: ${state.phase}`;
    document.getElementById("turnIndicator").innerText = `Turn: ${state.current_turn_player_id === playerId ? "Your Turn" : state.current_turn_player_id}`;

    // Clear player areas except center deck
    document.querySelectorAll(".playerArea").forEach(el => el.remove());

    // Render all players
    state.players.forEach(player => {
        if (player.username === username) {
            renderBottomHand(player.hand, player);
        } else {
            renderPlayer(player, state);
        }
    });

    // Update health display
    const me = state.players.find(p => p.username === username);
    if (me) {
        document.getElementById("health").textContent = `❤️ ${me.health}`;
    }
}

// function renderBottomHand(hand, player) {
//     bottomHand.innerHTML = "";
//     hand.forEach(card => {
//         const cardDiv = document.createElement("div");
//         cardDiv.className = "card";
//         cardDiv.textContent = card.type;
//         cardDiv.title = card.description;
//         cardDiv.onclick = () => playCard(card.id);
//         if (card.is_primed) cardDiv.style.border = "2px solid orange";
//         bottomHand.appendChild(cardDiv);
//     });
//     // Show status effects
//     showStatusEffects(player, bottomHand);
// }

function renderBottomHand(hand) {
    bottomHand.innerHTML = "";
    hand.forEach(card => {
        const cardDiv = document.createElement("div");
        cardDiv.className = "card";
        cardDiv.textContent = card.symbol || card.name;
        cardDiv.onclick = () => {
            if (isMyTurn && isPlayPhase) {
                showTargetModal(card.name, currentGameState.players); // Pass state.players
            } else {
                alert("Not your turn or not play phase.");
            }
        };
        bottomHand.appendChild(cardDiv);
    });
}


function renderPlayer(player, state) {
    const div = document.createElement("div");
    div.className = "playerArea";
    div.innerHTML = `
        <div class="avatar">${player.username[0]}</div>
        <div class="username">${player.username}${player.is_royal ? " 👑" : ""}</div>
        <div class="health">❤️ ${player.health}</div>
        <div class="status">${getStatusText(player)}</div>
        <div class="hand">
            ${player.hand.map(card => `<div class="card" title="${card.description}">${card.type}${card.is_primed ? " 🔥" : ""}</div>`).join("")}
        </div>
    `;
    gameArea.appendChild(div);
}

function getStatusText(player) {
    let status = [];
    if (player.eliminated) status.push("💀 Eliminated");
    if (player.snakebit) status.push("🐍 Snakebit");
    if (player.entranced) status.push("🔮 Entranced");
    if (player.is_primed) status.push("💣 Primed");
    if (player.shield > 0) status.push("🛡️ Shield x" + player.shield);
    return status.join(" | ");
}

function showStatusEffects(player, container) {
    let effects = [];
    if (player.snakebit) effects.push("🐍 Snakebit: skip next play");
    if (player.entranced) effects.push("🔮 Entranced: play face up");
    if (player.is_primed) effects.push("💣 Primed: bomb will explode");
    if (player.shield > 0) effects.push("🛡️ Shield x" + player.shield);
    if (effects.length) {
        const effDiv = document.createElement("div");
        effDiv.className = "effects";
        effDiv.textContent = effects.join(" | ");
        container.appendChild(effDiv);
    }
}

async function drawCard() {
    if (!isMyTurn || !isDrawPhase) {
    alert("Not your turn or wrong phase!");
    return;
  }
    try {
        const res = await fetch(`${API_BASE}/draw`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_code: gameCode, player_id: playerId })
        });
        const data = await res.json();
        fetchGameState();
    } catch (err) {
        alert("Failed to draw card: " + err.message);
    }
}

async function playCard(cardId) {
    try {
        const target = prompt("Enter target player's username:");
        if (!target) return;
        // Find target player id
        const state = await (await fetch(`${API_BASE}/game_state/${gameCode}`)).json();
        const targetPlayer = state.players.find(p => p.username === target);
        if (!targetPlayer) return alert("Player not found!");
        await fetch(`${API_BASE}/play_card`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_code: gameCode,
                player_id: playerId,
                card_id: cardName,
                target_id: target
                })

        });
        fetchGameState();
    } catch (err) {
        alert("Failed to play card: " + err.message);
    }
}

function showTargetModal(cardName, players) {
  const modal = document.getElementById("targetModal");
  const list = document.getElementById("targetList");
  list.innerHTML = "";

  players.forEach(p => {
    if (p.id !== playerId) {
      const btn = document.createElement("button");
      btn.innerText = p.username;
      btn.onclick = () => {
        modal.style.display = "none";
        playCard(cardName, p.id);
      };
      list.appendChild(btn);
    }
  });

  modal.style.display = "block";
}


function goToMenu() {
    window.location.href = "menu.html";
}

function toggleSettings() {
    const menu = document.getElementById("settingsMenu");
    menu.style.display = menu.style.display === "flex" ? "none" : "flex";
}

// function changeColor(color) {
//     const body = document.body;
//     body.classList.remove("theme-green", "theme-blue", "theme-red");
//     if (color === "#0a3d0a") body.classList.add("theme-green");
//     else if (color === "#112244") body.classList.add("theme-blue");
//     else if (color === "#441111") body.classList.add("theme-red");
// }

function changeColor(color) {
            document.body.style.backgroundColor = color;
        }

        

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("🔁 WS UPDATE:", data);  // See the updated game state in console
  renderGame(data);
};

// Initial fetch and poll fallback
fetchGameState();
setInterval(fetchGameState, 1000);