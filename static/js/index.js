document.addEventListener("DOMContentLoaded", function () {
  const leaderboardContainer = document.getElementById("leaderboard-container");
  const challengeStatusContainer = document.getElementById(
    "flag-status-container"
  );
  let previousLeaderboardData = null;
  let previousChallengeStatusData = null;
  const positionToNameElement = new Map();
  const positionToScoreElement = new Map();
  const challengeToStatusElement = new Map();

  // Add these at the top with your other constants
  const countdownElement = document.getElementById("countdown");
  let currentEpoch = null;
  let countdownInterval = null;

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

  function createLeaderboardEntry(entryData, index) {
    const entryDiv = document.createElement("div");
    entryDiv.classList.add("leaderboard-entry");
    entryDiv.dataset.position = index;

    const userInfoDiv = document.createElement("div");
    userInfoDiv.classList.add("user-info");

    const placeSpan = document.createElement("span");
    placeSpan.textContent = getPlaceString(index + 1);
    placeSpan.classList.add("place");
    userInfoDiv.appendChild(placeSpan);

    const teamNameSpan = document.createElement("span");
    teamNameSpan.textContent = entryData.team;
    teamNameSpan.classList.add("team-name");
    userInfoDiv.appendChild(teamNameSpan);
    positionToNameElement.set(index, teamNameSpan);

    entryDiv.appendChild(userInfoDiv);

    const scoreDiv = document.createElement("div");
    scoreDiv.classList.add("score");
    const scoreSpan = document.createElement("span");
    scoreSpan.textContent = entryData.score;
    scoreSpan.classList.add("score-value");
    scoreDiv.appendChild(scoreSpan);
    entryDiv.appendChild(scoreDiv);
    positionToScoreElement.set(index, scoreSpan);

    return entryDiv;
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

  function createChallengeStatusEntry(challengeName, solvingTeam) {
    const entryDiv = document.createElement("div");
    entryDiv.classList.add("challenge-status");

    const challengeNameDiv = document.createElement("div");
    challengeNameDiv.classList.add("challenge-name");
    challengeNameDiv.textContent = challengeName;
    entryDiv.appendChild(challengeNameDiv);

    const challengeStatusTextDiv = document.createElement("div");
    challengeStatusTextDiv.classList.add("challenge-status-text");
    challengeStatusTextDiv.setAttribute("data-animatable", "true");
    challengeStatusTextDiv.textContent = solvingTeam
      ? `${solvingTeam}`
      : "Unsolved";
    if (!solvingTeam) {
      challengeStatusTextDiv.classList.add("unsolved");
    }
    entryDiv.appendChild(challengeStatusTextDiv);

    challengeToStatusElement.set(challengeName, challengeStatusTextDiv);

    return entryDiv;
  }

  function populateLeaderboard(leaderboardData) {
    leaderboardContainer.innerHTML = "";
    positionToNameElement.clear();
    positionToScoreElement.clear();
    leaderboardData.forEach((entry, index) => {
      const entryElement = createLeaderboardEntry(entry, index);
      leaderboardContainer.appendChild(entryElement);
    });
  }

  function populateChallengeStatus(challengeStatusData) {
    challengeStatusContainer.innerHTML = "";
    challengeToStatusElement.clear();
    for (const challengeName in challengeStatusData) {
      if (challengeStatusData.hasOwnProperty(challengeName)) {
        const solvingTeam = challengeStatusData[challengeName];
        const challengeElement = createChallengeStatusEntry(
          challengeName,
          solvingTeam
        );
        challengeStatusContainer.appendChild(challengeElement);
      }
    }
  }

  function triggerTextEffect(element, newText) {
    return new Promise((resolve) => {
      const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789";
      const randEnd = 30;

      if (!element) {
        console.warn("No element found to apply the effect.");
        resolve();
        return;
      }

      const originalText = element.innerText;
      let iterations = 0;
      const maxLength = Math.max(originalText.length, newText.length);

      const interval = setInterval(() => {
        const newCharacters = [];

        for (let i = 0; i < maxLength; i++) {
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

        if (iterations >= maxLength + randEnd) {
          clearInterval(interval);
          element.innerText = newText;
          resolve();
        }

        iterations += 1 / 3;
      }, 10);
    });
  }

  function getPositionChanges(prevData, newData) {
    if (!prevData || !newData) {
      return { nameChanges: [], scoreChanges: [] };
    }

    const nameChanges = [];
    const scoreChanges = [];

    for (
      let position = 0;
      position < Math.max(prevData.length, newData.length);
      position++
    ) {
      if (!prevData[position] || !newData[position]) continue;

      if (prevData[position].team !== newData[position].team) {
        nameChanges.push({
          position: position,
          oldText: prevData[position].team,
          newText: newData[position].team,
        });

        scoreChanges.push({
          position: position,
          oldText: prevData[position].score.toString(),
          newText: newData[position].score.toString(),
        });
      } else if (prevData[position].score !== newData[position].score) {
        scoreChanges.push({
          position: position,
          oldText: prevData[position].score.toString(),
          newText: newData[position].score.toString(),
        });
      }
    }

    return { nameChanges, scoreChanges };
  }

  function getChallengeStatusChanges(prevData, newData) {
    if (!prevData || !newData) {
      return [];
    }

    const statusChanges = [];

    for (const challengeName in newData) {
      if (
        prevData.hasOwnProperty(challengeName) &&
        prevData[challengeName] !== newData[challengeName]
      ) {
        statusChanges.push({
          challengeName: challengeName,
          oldText: prevData[challengeName] || "Unsolved",
          newText: newData[challengeName] || "Unsolved",
        });
      }
    }

    return statusChanges;
  }

  async function updateData() {
    try {
      const leaderboardResponse = await fetch("/api/leaderboard");
      const newLeaderboardData = await leaderboardResponse.json();

      const flagStatusResponse = await fetch("/api/flag-status");
      const newFlagStatusData = await flagStatusResponse.json();

      const epochResponse = await fetch("/api/end-time");
      const epochData = await epochResponse.json();

      // Update epoch and restart countdown if it's different
      if (currentEpoch !== epochData.epoch) {
        currentEpoch = epochData.epoch;

        // Clear existing interval if it exists
        if (countdownInterval) {
          clearInterval(countdownInterval);
        }

        // Start new countdown
        updateCountdown();
        countdownInterval = setInterval(updateCountdown, 1000);
      }

      if (!previousLeaderboardData || !previousChallengeStatusData) {
        populateLeaderboard(newLeaderboardData);
        populateChallengeStatus(newFlagStatusData);
        previousLeaderboardData = JSON.parse(
          JSON.stringify(newLeaderboardData)
        );
        previousChallengeStatusData = JSON.parse(
          JSON.stringify(newFlagStatusData)
        );
        return;
      }

      const { nameChanges, scoreChanges } = getPositionChanges(
        previousLeaderboardData,
        newLeaderboardData
      );

      const challengeChanges = getChallengeStatusChanges(
        previousChallengeStatusData,
        newFlagStatusData
      );

      const effectPromises = [];

      nameChanges.forEach((change) => {
        const nameElement = positionToNameElement.get(change.position);
        if (nameElement) {
          effectPromises.push(triggerTextEffect(nameElement, change.newText));
        }
      });

      scoreChanges.forEach((change) => {
        const scoreElement = positionToScoreElement.get(change.position);
        if (scoreElement) {
          effectPromises.push(triggerTextEffect(scoreElement, change.newText));
        }
      });

      challengeChanges.forEach((change) => {
        const statusElement = challengeToStatusElement.get(
          change.challengeName
        );
        if (statusElement) {
          effectPromises.push(triggerTextEffect(statusElement, change.newText));

          if (change.newText === "Unsolved") {
            statusElement.classList.add("unsolved");
          } else {
            statusElement.classList.remove("unsolved");
          }
        }
      });

      await Promise.all(effectPromises);

      populateLeaderboard(newLeaderboardData);
      populateChallengeStatus(newFlagStatusData);

      previousLeaderboardData = JSON.parse(JSON.stringify(newLeaderboardData));
      previousChallengeStatusData = JSON.parse(
        JSON.stringify(newFlagStatusData)
      );
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }

  updateData();
  setInterval(updateData, 5000);
});
