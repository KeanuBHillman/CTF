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
  const submitButton = document.getElementById("submit-flag");
  const teamInput = document.getElementById("team-input");
  const flagInput = document.getElementById("flag-input");

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

  // --- Helper: render a challenge into the modal ---
  function showChallenge(index) {
    currentIndex = index;
    const challengeData = challenges[index];

    document.getElementById("modal-title").textContent = challengeData.title;
    document.getElementById(
      "modal-points"
    ).textContent = `${challengeData.points} points`;

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
  fetch("/api/challenges")
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
        `
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

  // --- Optional: Submit flag ---
  if (submitButton) {
    submitButton.addEventListener("click", () => {
      const flagValue = flagInput.value.trim();
      const responseBox = document.getElementById("response-box");
      const responseText = document.getElementById("response-text");

      // Reset box
      responseBox.style.display = "none";
      responseBox.className = "response-box";

      if (!flagValue) {
        responseText.textContent = "No Flag";
        responseBox.classList.add("response-error");
        responseBox.style.display = "flex";
        return;
      }

      fetch("/submit_flag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flagValue }),
      })
        .then(async (res) => {
          const result = await res.json();
          responseText.textContent = result.message || "No response message";

          if (res.status === 200) {
            responseBox.classList.add("response-success");
            flagInput.value = "";
          } else {
            responseBox.classList.add("response-error");
          }

          responseBox.style.display = "flex";
        })
        .catch((err) => {
          responseText.textContent = "Server error, please try again.";
          responseBox.classList.add("response-error");
          responseBox.style.display = "flex";
          console.error("Error submitting flag:", err);
        });
    });
  }

  async function updateData() {
    const challengeResponse = await fetch("/api/challenges");
    const challengeData = await challengeResponse.json()
    for (let challengeId in challengeData) {
      element = document.getElementById(`challenge-status-challenge-${challengeId}`)
      const state = challengeData[challengeId].solved ? "Solved" : "Unsolved"
      if (element.innerHTML !== state) {
        animateTextChange(element, state)
      }
    }
  }
  setInterval(updateData, 5000);
});
