const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789";
const randEnd = 30;

document.addEventListener("DOMContentLoaded", () => {
  const challengeListDiv = document.getElementById("challenge-list");
  const modalDiv = document.getElementById("modal");
  const modalTitle = document.getElementById("modal-title");
  const modalDescription = document.getElementById("modal-description");
  const closeBtn = document.getElementById("modal-close");
  const upBtn = document.getElementById("modal-up");
  const downBtn = document.getElementById("modal-down");
  const startChallengeButton = document.getElementById("start-challenge");
  const teamInput = document.getElementById("team-input");

  let challenges = [];
  let currentIndex = 0;

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
              letters[Math.floor(Math.random() * letters.length)],
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

  // --- Helper: render a challenge into the modal ---
  function showChallenge(index) {
    currentIndex = index;
    const challengeData = challenges[index];

    document.getElementById("modal-title").textContent = challengeData.title;
    document.getElementById("modal-points").textContent =
      `${challengeData.points} points`;

    const difficultyEl = document.getElementById("modal-difficulty");
    difficultyEl.textContent = challengeData.difficulty;

    // Reset difficulty classes
    difficultyEl.className = "challenge-difficulty";

    // Apply color class based on difficulty
    switch (challengeData.difficulty.toLowerCase()) {
      case "very easy":
        difficultyEl.classList.add("difficulty-veryeasy");
        break;
      case "easy":
        difficultyEl.classList.add("difficulty-easy");
        break;
      case "medium":
        difficultyEl.classList.add("difficulty-medium");
        break;
      case "hard":
        difficultyEl.classList.add("difficulty-hard");
        break;
      case "impossible":
        difficultyEl.classList.add("difficulty-veryhard");
        break;
    }

    modalDescription.innerHTML = challengeData.description;

    // Enhance code blocks with copy buttons
    modalDescription.querySelectorAll("code").forEach((codeBlock) => {
      const button = document.createElement("button");
      button.className = "code-copy-btn";
      button.textContent = "Copy";

      codeBlock.style.position = "relative";
      codeBlock.appendChild(button);

      button.addEventListener("click", () => {
        const text = codeBlock.textContent;
        navigator.clipboard.writeText(text).then(() => {
          button.textContent = "Copied!";
          setTimeout(() => (button.textContent = "Copy"), 1500);
        });
      });
    });

    modalDiv.style.display = "flex";
  }

  // --- Fetch challenges from API ---
  fetch("/api/challenges/")
    .then((response) => response.json())
    .then((data) => {
      challenges = data;

      // Render challenge list
      challengeListDiv.innerHTML = challenges
        .map(
          (challenge, index) => `
          <div class="challenge-status" data-index="${index}">
            <div class="challenge-name">${challenge.title}</div>
            <div class="challenge-unsolved" id="challenge-status-challenge-${challenge.id}">${
              challenge.solved ? "Solved" : "Unsolved"
            }</div>
          </div>
        `,
        )
        .join("");

      // Add click listeners to open modal
      document.querySelectorAll(".challenge-status").forEach((el) => {
        el.addEventListener("click", () => {
          const index = parseInt(el.dataset.index, 10);
          showChallenge(index);
        });
      });
    })
    .catch((error) => console.error("Error loading JSON:", error));

  // --- Footer Buttons ---
  upBtn.addEventListener("click", () => {
    const newIndex =
      currentIndex > 0 ? currentIndex - 1 : challenges.length - 1; // loop back
    showChallenge(newIndex);
  });

  downBtn.addEventListener("click", () => {
    const newIndex =
      currentIndex < challenges.length - 1 ? currentIndex + 1 : 0; // loop back
    showChallenge(newIndex);
  });

  closeBtn.addEventListener("click", () => {
    modalDiv.style.display = "none";
  });

  // --- Start Challenge Button ---
  if (startChallengeButton) {
    startChallengeButton.addEventListener("click", () => {
      console.log("Start challenge button clicked");
      console.log("Current index:", currentIndex);
      console.log("Challenges:", challenges);
      
      if (challenges.length === 0) {
        alert("Challenges not loaded yet. Please wait a moment and try again.");
        return;
      }
      
      if (!challenges[currentIndex]) {
        alert("Invalid challenge selected.");
        return;
      }
      
      const challengeId = challenges[currentIndex].id;
      const challengeTitle = challenges[currentIndex].title;
      
      console.log("Redirecting to challenge:", challengeId, challengeTitle);
      
      // Redirect to challenge-specific questions page
      window.location.href = `/challenge/${challengeId}/questions`;
    });
  } else {
    console.error("Start challenge button not found");
  }

  async function updateData() {
    const challengeResponse = await fetch("/api/challenges/");
    const challengeData = await challengeResponse.json();

    challengeData.forEach((challenge) => {
      const element = document.getElementById(
        `challenge-status-challenge-${challenge.id}`,
      );

      if (!element) return; // prevent crash

      const state = challenge.solved ? "Solved" : "Unsolved";

      if (element.innerHTML !== state) {
        animateTextChange(element, state);
      }
    });
  }

  setInterval(updateData, 5000);
});
