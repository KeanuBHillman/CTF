const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789";
const randEnd = 30;

const leaderboardIndexToNameElement = new Map();
const leaderboardIndexToScoreElement = new Map();
const leaderboardIndexToPositionElement = new Map();
const flagIndexToStatusElement = new Map();

let currentEpoch = null;

document.addEventListener("DOMContentLoaded", function () {
  const leaderboardContainer = document.getElementById("leaderboard-container");
  const flagStatusContainer = document.getElementById("flag-status-container");
  const countdownElement = document.getElementById("countdown");

  function formatTime(seconds) {
    if (seconds < 0) return "00:00:00";

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours
      .toString()
      .padStart(
        2,
        "0"
      )}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  function updateCountdown() {
    if (currentEpoch === null) return;

    const now = Math.floor(Date.now() / 1000);
    const remaining = currentEpoch - now;
    countdownElement.textContent = formatTime(remaining);
  }

  function getPlaceString(place) {
    if (place % 10 === 1 && place % 100 !== 11) {
      return place + "ST";
    } else if (place % 10 === 2 && place % 100 !== 12) {
      return place + "ND";
    } else if (place % 10 === 3 && place % 100 !== 13) {
      return place + "RD";
    } else {
      return place + "TH";
    }
  }

  function createLeaderboardEntry(index, entryData) {
    const entryDiv = document.createElement("div");
    entryDiv.classList.add("leaderboard__team-entry");
    entryDiv.dataset.position = index;

    const teamInfoDiv = document.createElement("div");
    teamInfoDiv.classList.add("leaderboard__team-info");

    const positionSpan = document.createElement("span");
    positionSpan.textContent = getPlaceString(entryData.position);
    positionSpan.classList.add("leaderboard__team-position");
    leaderboardIndexToPositionElement.set(index, positionSpan);
    teamInfoDiv.appendChild(positionSpan);

    const teamNameSpan = document.createElement("span");
    teamNameSpan.textContent = entryData.team;
    teamNameSpan.classList.add("leaderboard__team-name");
    teamInfoDiv.appendChild(teamNameSpan);
    leaderboardIndexToNameElement.set(index, teamNameSpan);

    entryDiv.appendChild(teamInfoDiv);

    const pointsDiv = document.createElement("div");
    pointsDiv.classList.add("points");
    const pointsSpan = document.createElement("span");
    pointsSpan.textContent = entryData.score;
    pointsSpan.classList.add("points-value");
    pointsDiv.appendChild(pointsSpan);
    entryDiv.appendChild(pointsDiv);
    leaderboardIndexToScoreElement.set(index, pointsSpan);

    return entryDiv;
  }

  function animateTextChange(element, newText) {
    return new Promise((resolve) => {
      if (!element) {
        console.warn("No element found to apply the effect.");
        resolve();
        return;
      }

      const originalText = element.innerText;
      let iterations = 0;
      const newLength = Math.max(originalText.length, newText.length);

      const interval = setInterval(() => {
        const newCharacters = [];

        for (let i = 0; i < newLength; i++) {
          if (iterations > i + randEnd) {
            newCharacters.push(i < newText.length ? newText[i] : "");
          } else if (iterations > i) {
            newCharacters.push(
              letters[Math.floor(Math.random() * letters.length)]
            );
          } else {
            newCharacters.push(i < originalText.length ? originalText[i] : "");
          }
        }

        element.innerText = newCharacters.join("");

        if (iterations >= newLength * 2 + randEnd) {
          clearInterval(interval);
          element.innerText = newText;
          resolve();
        }

        iterations += 1;
      }, 30);
    });
  }

  function updateLeaderboardEntry(index, data) {
    const nameElement = leaderboardIndexToNameElement.get(index);
    const scoreElement = leaderboardIndexToScoreElement.get(index);
    const positionElement = leaderboardIndexToPositionElement.get(index);

    if (nameElement && scoreElement && positionElement) {
      if (!(nameElement.textContent === data.teamName)) {
        animateTextChange(nameElement, data.teamName);
      }
      if (scoreElement.textContent !== String(data.points)) {
        animateTextChange(scoreElement, String(data.points));
      }
      newPosition = getPlaceString(data.position);
      if (!(positionElement.textContent == newPosition)) {
        animateTextChange(positionElement, newPosition);
      }
    }
  }

  function updateLeaderboard(newData) {
    // Remove excess entries if new data is shorter
    while (leaderboardIndexToNameElement.size > newData.length) {
      const lastIndex = leaderboardIndexToNameElement.size - 1;
      // Remove DOM element
      leaderboardIndexToNameElement
        .get(lastIndex)
        ?.closest(".leaderboard__team-entry")
        ?.remove();
      // Clean up maps
      leaderboardIndexToNameElement.delete(lastIndex);
      leaderboardIndexToScoreElement.delete(lastIndex);
    }

    // Update or add entries
    newData.forEach((team, index) => {
      if (leaderboardIndexToNameElement.has(index)) {
        // Update existing entry
        updateLeaderboardEntry(index, team);
      } else {
        // Create new entry
        const entry = createLeaderboardEntry(index, team);
        leaderboardContainer.appendChild(entry);
        updateLeaderboardEntry(index, team);
      }
    });
  }

  function createFlagStatusEntry(data) {
    const entryDiv = document.createElement("div");
    entryDiv.classList.add("flag-status__entry");

    const flagNameDiv = document.createElement("div");
    flagNameDiv.classList.add("flag-status__flag_name");
    flagNameDiv.textContent = data.name;
    entryDiv.appendChild(flagNameDiv);

    const flagStatusTextDiv = document.createElement("div");
    flagStatusTextDiv.classList.add("flag-status__status");
    flagStatusTextDiv.setAttribute("data-animatable", "true");
    flagStatusTextDiv.textContent = "Unsolved";
    flagStatusTextDiv.classList.add("unsolved");

    entryDiv.appendChild(flagStatusTextDiv);

    flagIndexToStatusElement.set(data.name, flagStatusTextDiv);

    return entryDiv;
  }

  function updateFlagStatusEntry(flagId, data) {
    const statusElement = flagIndexToStatusElement.get(data.name);

    if (statusElement) {
      const newStatus = data.team ? `${data.team}` : "Unsolved";

      if (statusElement.textContent !== newStatus) {
        animateTextChange(statusElement, newStatus);

        // Toggle unsolved class
        if (data.team) {
          statusElement.classList.remove("unsolved");
        } else {
          statusElement.classList.add("unsolved");
        }
      }
    }
  }

  function updateFlagStatus(newData) {
    const entries = Object.entries(newData).reverse();
    // Update entries
    entries.forEach(([flagId, data]) => {
      if (flagIndexToStatusElement.has(data.name)) {
        // Update existing entry
        updateFlagStatusEntry(flagId, data);
      } else {
        // Create new entry
        const entry = createFlagStatusEntry(data);
        flagStatusContainer.appendChild(entry);
        updateFlagStatusEntry(flagId, data);
      }
    });
  }

  function updateCountdown() {
    if (currentEpoch === null) return;

    const now = Math.floor(Date.now() / 1000);
    const remaining = currentEpoch - now;
    countdownElement.textContent = formatTime(remaining);
  }

  async function updateData() {
    const leaderboardResponse = await fetch("/api/leaderboard");
    const newLeaderboardData = await leaderboardResponse.json();

    updateLeaderboard(newLeaderboardData);

    const flagStatusResponse = await fetch("/api/flag-status");
    const newFlagStatusData = await flagStatusResponse.json();

    updateFlagStatus(newFlagStatusData);
  }
  async function updateTime() {
    const epochResponse = await fetch("/api/end-time");
    const epochData = await epochResponse.json();

    currentEpoch = epochData.epoch;
  }
  updateData();
  updateTime();
  setInterval(updateData, 5000);
  setInterval(updateTime, 30000);
  setInterval(updateCountdown, 1000);
});
