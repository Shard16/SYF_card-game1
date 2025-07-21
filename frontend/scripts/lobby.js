let gameCode = null;
let isHost = false;
let username = null;

const codeDiv = document.getElementById('code');
const generateBtn = document.getElementById('generate-btn');
const copyBtn = document.getElementById('copy-btn');
const startBtn = document.getElementById('start-btn');
const playersDiv = document.getElementById('players');

function showCode() {
    codeDiv.textContent = gameCode || "";
    if (gameCode) {
        copyBtn.style.display = '';
        startBtn.style.display = '';
    }
}


generateBtn.onclick = async() => {
    username = prompt("Enter your name:");
    if (!username) return;
    const res = await fetch('/create_game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });
    const data = await res.json();
    gameCode = data.game_code;
    isHost = true;
    localStorage.setItem("game_code", gameCode);
    localStorage.setItem("username", username);
    showCode();
    await joinGame(username);
    fetchPlayers();
    setInterval(fetchPlayers, 1500);

};

const joinBtn = document.getElementById('join-btn');
joinBtn.onclick = async() => {
    const code = document.getElementById("joinKey").value.trim().toUpperCase();
    const username = prompt("Enter your name:");
    if (!code || !username) return alert("Enter a valid code and name!");
    gameCode = code;
    localStorage.setItem("game_code", gameCode);
    localStorage.setItem("username", username);
    await joinGame(username);
    fetchPlayers();
    setInterval(fetchPlayers, 1500);
    showCode();
};

copyBtn.onclick = () => {
    navigator.clipboard.writeText(gameCode);
    copyBtn.textContent = "Copied!";
    setTimeout(() => (copyBtn.textContent = "Copy Code"), 1000);
};

async function joinGame(name) {
    await fetch('/join_game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_code: gameCode, username: name })
    });
}

async function fetchPlayers() {
    if (!gameCode) return;
    const res = await fetch(`/players/${gameCode}`);
    const players = await res.json();
    playersDiv.innerHTML =
        '<b>Players:</b><br>' + players.map(p => p.username).join('<br>');
}

startBtn.onclick = () => {
    window.location.href = `waiting.html?code=${gameCode}&host=1`;
};

// If joining via code (not host)
window.onload = async() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('code')) {
        gameCode = urlParams.get('code');
        isHost = urlParams.get('host') === '1';
        username = prompt("Enter your name:");
        if (username) {
            localStorage.setItem("game_code", gameCode);
            localStorage.setItem("username", username);
            await joinGame(username);
            showCode();
            fetchPlayers();
            setInterval(fetchPlayers, 1500);
        }
    }
};