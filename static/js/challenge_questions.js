document.addEventListener("DOMContentLoaded", () => {

  // setting up input handling for date, coordinate, and time blocks with strict validation on format and values
  const DATE_FORMAT_REGEX = /^\d{4} - \d{2} - \d{2}$/;
  const COORD_FORMAT_REGEX = /^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$/;
  const TIME_FORMAT_REGEX = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

  function isValidStrictDate(value) {
    if (!DATE_FORMAT_REGEX.test(value)) {
      return false;
    }

    const [yearText, monthText, dayText] = value.split(" - ");
    const year = Number(yearText);
    const month = Number(monthText);
    const day = Number(dayText);

    const candidate = new Date(Date.UTC(year, month - 1, day));
    return (
      candidate.getUTCFullYear() === year &&
      candidate.getUTCMonth() === month - 1 &&
      candidate.getUTCDate() === day
    );
  }

  function isValidCoordinates(value) {
    if (!COORD_FORMAT_REGEX.test(value)) {
      return false;
    }
    const [latStr, lngStr] = value.split(",");
    const lat = parseFloat(latStr);
    const lng = parseFloat(lngStr);
    return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  }

  function isValidTime(value) {
    return TIME_FORMAT_REGEX.test(value);
  }

  function setupDateBlockInputs() {
    const blocks = document.querySelectorAll("[data-date-block='true']");
    blocks.forEach((block) => {
      const yearInput = block.querySelector("[data-date-part='year']");
      const monthInput = block.querySelector("[data-date-part='month']");
      const dayInput = block.querySelector("[data-date-part='day']");
      const parts = [yearInput, monthInput, dayInput];

      parts.forEach((input, index) => {
        const maxLength = Number(input.getAttribute("maxlength"));

        input.addEventListener("input", () => {
          input.value = input.value.replace(/\D/g, "").slice(0, maxLength);
          if (input.value.length === maxLength && index < parts.length - 1) {
            parts[index + 1].focus();
          }
        });

        input.addEventListener("keydown", (event) => {
          if (event.key === "Backspace" && !input.value && index > 0) {
            parts[index - 1].focus();
          }
        });
      });
    });
  }

  function setupCoordinateBlockInputs() {
    const blocks = document.querySelectorAll("[data-coord-block='true']");
    blocks.forEach((block) => {
      const latInput = block.querySelector("[data-coord-part='lat']");
      const lngInput = block.querySelector("[data-coord-part='lng']");

      if (latInput && lngInput) {
        const setupNumericInput = (input) => {
          input.addEventListener("input", () => {
            input.value = input.value.replace(/[^0-9.\-]/g, "");
            const parts = input.value.split(".");
            if (parts.length > 2) {
              input.value = parts[0] + "." + parts.slice(1).join("");
            }
          });
        };
        setupNumericInput(latInput);
        setupNumericInput(lngInput);
      }
    });
  }

  function setupTimeBlockInputs() {
    const blocks = document.querySelectorAll("[data-time-block='true']");
    blocks.forEach((block) => {
      const hourInput = block.querySelector("[data-time-part='hour']");
      const minuteInput = block.querySelector("[data-time-part='minute']");
      const parts = [hourInput, minuteInput];

      parts.forEach((input, index) => {
        const maxLength = Number(input.getAttribute("maxlength"));

        input.addEventListener("input", () => {
          input.value = input.value.replace(/\D/g, "").slice(0, maxLength);
          if (input.value.length === maxLength && index < parts.length - 1) {
            parts[index + 1].focus();
          }
        });

        input.addEventListener("keydown", (event) => {
          if (event.key === "Backspace" && !input.value && index > 0) {
            parts[index - 1].focus();
          }
        });
      });
    });
  }

  // Get challenge ID from URL
  const pathParts = window.location.pathname.split('/');
  const challengeId = pathParts[2]; // /challenge/{id}/questions
  
  const challengeTitle = document.getElementById("challenge-title");
  const challengePoints = document.getElementById("challenge-points");
  const challengeDifficulty = document.getElementById("challenge-difficulty");
  const challengeDescription = document.getElementById("challenge-description");
  const questionsList = document.getElementById("questions-list");
  const submitButton = document.getElementById("submit-answers");
  const backButton = document.getElementById("back-to-challenges");
  const responseBox = document.getElementById("response-box");
  const responseText = document.getElementById("response-text");

  let challengeData = null;
  let questions = [];

  // Load challenge data
  fetch(`/api/challenges/`)
    .then(response => response.json())
    .then(data => {
      // Find the specific challenge
      challengeData = data.find(c => c.id == challengeId);
      
      if (!challengeData) {
        challengeTitle.textContent = "Challenge Not Found";
        challengeDescription.textContent = "The requested challenge could not be found.";
        return;
      }

      // Update challenge info
      challengeTitle.textContent = challengeData.title;
      challengePoints.textContent = `${challengeData.points} points`;
      challengeDifficulty.textContent = challengeData.difficulty;
      challengeDescription.innerHTML = challengeData.description;

      // Apply difficulty styling
      challengeDifficulty.className = `challenge-difficulty difficulty-${challengeData.difficulty.toLowerCase().replace(' ', '')}`;

      // Load questions for this challenge
      loadQuestions();
    })
    .catch(error => {
      console.error("Error loading challenge:", error);
      challengeTitle.textContent = "Error Loading Challenge";
      challengeDescription.textContent = "Failed to load challenge data.";
    });

  // Load questions from database for this specific challenge
  function loadQuestions() {
    fetch(`/api/challenges/${challengeId}/questions`)
      .then(response => response.json())
      .then(data => {
        // Use questions from database (may be empty for some challenges)
        questions = Array.isArray(data) ? data : [];
        renderQuestions();
      })
      .catch(error => {
        console.error("Error loading questions:", error);
        questions = [];
        showResponse("Could not load questions for this challenge.", "error");
        renderQuestions();
      });
  }

  function renderQuestions() {
    if (!questions || questions.length === 0) {
      questionsList.innerHTML = '<div class="question-item"><label class="question-label">No questions are configured for this challenge yet.</label></div>';
      if (challengePoints) {
        challengePoints.innerHTML = `<strong>0 points</strong> <small>(0 questions)</small>`;
      }
      return;
    }

    const totalPoints = questions.reduce((sum, q) => sum + (q.points || 0), 0);
    
    // Update challenge points with breakdown
    if (challengePoints && totalPoints > 0) {
      challengePoints.innerHTML = `<strong>${totalPoints} points</strong> <small>(${questions.length} questions)</small>`;
    }
    
    questionsList.innerHTML = questions.map((q, index) => {
      let inputHtml = "";

      if (q.question_type === 'single_select' || (q.answer_type === 'multiple_choice' && Array.isArray(q.options) && q.options.length > 0)) {
        const optionTags = q.options
          .map(option => `<option value="${option}">${option}</option>`)
          .join('');

        inputHtml = `
          <select id="question-${q.id}">
            <option value="">Select an option...</option>
            ${optionTags}
          </select>
        `;
      } else if (q.question_type === 'textarea') {
        inputHtml = `<textarea id="question-${q.id}" rows="4" placeholder="Your answer..."></textarea>`;
      } else if (q.question_type === 'date_blocks') {
        inputHtml = `
          <div class="date-block-input" data-date-block="true" data-question-id="${q.id}">
            <input type="text" id="question-${q.id}-year" data-date-part="year" maxlength="4" inputmode="numeric" placeholder="YYYY" aria-label="Year" />
            <span class="date-separator">-</span>
            <input type="text" id="question-${q.id}-month" data-date-part="month" maxlength="2" inputmode="numeric" placeholder="MM" aria-label="Month" />
            <span class="date-separator">-</span>
            <input type="text" id="question-${q.id}-day" data-date-part="day" maxlength="2" inputmode="numeric" placeholder="DD" aria-label="Day" />
          </div>`;
      } else if (q.question_type === 'coordinate_blocks') {
        inputHtml = `
          <div class="coord-block-input" data-coord-block="true" data-question-id="${q.id}">
            <input type="text" id="question-${q.id}-lat" data-coord-part="lat" inputmode="decimal" placeholder="Latitude (-90 to 90)" aria-label="Latitude" />
            <span class="coord-separator">,</span>
            <input type="text" id="question-${q.id}-lng" data-coord-part="lng" inputmode="decimal" placeholder="Longitude (-180 to 180)" aria-label="Longitude" />
          </div>`;
      } else if (q.question_type === 'time_blocks') {
        inputHtml = `
          <div class="time-block-input" data-time-block="true" data-question-id="${q.id}">
            <input type="text" id="question-${q.id}-hour" data-time-part="hour" maxlength="2" inputmode="numeric" placeholder="HH" aria-label="Hour" />
            <span class="time-separator">:</span>
            <input type="text" id="question-${q.id}-minute" data-time-part="minute" maxlength="2" inputmode="numeric" placeholder="MM" aria-label="Minute" />
          </div>`;
      } else {
        inputHtml = `<input type="text" id="question-${q.id}" placeholder="Your answer..." />`;
      }

      return `
      <div class="question-item">
        <label class="question-label">
          ${index + 1}. ${q.question_text} 
          ${q.required ? '<span class="required">*</span>' : ''}
          <span class="question-points">${q.points || 10} pts</span>
        </label>
        ${q.instructions ? `<div class="question-instructions">${q.instructions}</div>` : ''}
        ${inputHtml}
      </div>
    `;
    }).join('');

    setupDateBlockInputs();
    setupCoordinateBlockInputs();
    setupTimeBlockInputs();
  }

  // Submit answers
  submitButton.addEventListener("click", () => {
    const answers = {};
    let hasError = false;
    let dateFormatError = false;

    // Collect answers
    questions.forEach(q => {
      let input = document.getElementById(`question-${q.id}`);
      let value = input ? input.value.trim() : "";

      if (q.question_type === "date_blocks") {
        const yearInput = document.getElementById(`question-${q.id}-year`);
        const monthInput = document.getElementById(`question-${q.id}-month`);
        const dayInput = document.getElementById(`question-${q.id}-day`);

        if (yearInput && monthInput && dayInput) {
          const year = yearInput.value.trim();
          const month = monthInput.value.trim();
          const day = dayInput.value.trim();
          value = (year || month || day) ? `${year} - ${month} - ${day}` : "";
          input = yearInput;
        }
      } else if (q.question_type === "coordinate_blocks") {
        const latInput = document.getElementById(`question-${q.id}-lat`);
        const lngInput = document.getElementById(`question-${q.id}-lng`);

        if (latInput && lngInput) {
          const lat = latInput.value.trim();
          const lng = lngInput.value.trim();
          value = (lat || lng) ? `${lat},${lng}` : "";
          input = latInput;
        }
      } else if (q.question_type === "time_blocks") {
        const hourInput = document.getElementById(`question-${q.id}-hour`);
        const minuteInput = document.getElementById(`question-${q.id}-minute`);

        if (hourInput && minuteInput) {
          const hour = hourInput.value.trim();
          const minute = minuteInput.value.trim();
          value = (hour || minute) ? `${hour}:${minute}` : "";
          input = hourInput;
        }
      }
      
      if (q.required && !value) {
        input.style.borderColor = "red";
        hasError = true;
      } else if (value && q.question_type === "date_blocks" && !isValidStrictDate(value)) {
        input.style.borderColor = "red";
        hasError = true;
        dateFormatError = true;
      } else if (value && q.question_type === "coordinate_blocks" && !isValidCoordinates(value)) {
        input.style.borderColor = "red";
        hasError = true;
        dateFormatError = true;
      } else if (value && q.question_type === "time_blocks" && !isValidTime(value)) {
        input.style.borderColor = "red";
        hasError = true;
        dateFormatError = true;
      } else {
        input.style.borderColor = "";
        answers[q.id] = value;
      }
    });

    if (hasError) {
      showResponse(
        dateFormatError
          ? "Please check your format. Use YYYY - MM - DD for dates, HH:MM for time, or lat,lng for coordinates."
          : "Please answer all required questions.",
        "error"
      );
      return;
    }

    // Submit answers to server with new points-based API
    fetch(`/api/challenges/${challengeId}/submit-questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answers: answers
      })
    })
    .then(async (res) => {
      const result = await res.json();
      
      if (res.status === 200) {
        // Show points breakdown
        let message = `Submission complete!\n`;
        message += `Points earned: ${result.total_points_earned}\n`;
        message += `Questions answered: ${result.questions_answered}\n\n`;
        
        if (result.breakdown && result.breakdown.length > 0) {
          message += "Breakdown:\n";
          result.breakdown.forEach(item => {
            const status = item.status === "new" ? " NEW" : 
                          item.status === "already_answered" ? " ALREADY ANSWERED" :
                          item.status === "not_answered" ? " NOT ANSWERED" : " REQUIRED MISSING";
            message += `• ${item.points_awarded} pts - ${status}\n`;
          });
        }
        
        showResponse(message, "success");
        
        // Clear form after successful submission
        questions.forEach(q => {
          if (q.question_type === "date_blocks") {
            document.getElementById(`question-${q.id}-year`).value = "";
            document.getElementById(`question-${q.id}-month`).value = "";
            document.getElementById(`question-${q.id}-day`).value = "";
          } else if (q.question_type === "coordinate_blocks") {
            document.getElementById(`question-${q.id}-lat`).value = "";
            document.getElementById(`question-${q.id}-lng`).value = "";
          } else if (q.question_type === "time_blocks") {
            document.getElementById(`question-${q.id}-hour`).value = "";
            document.getElementById(`question-${q.id}-minute`).value = "";
          } else {
            const input = document.getElementById(`question-${q.id}`);
            if (input) input.value = "";
          }
        });
      } else {
        showResponse(result.detail || "Submission failed.", "error");
      }
    })
    .catch(error => {
      console.error("Error submitting answers:", error);
      showResponse("Server error, please try again.", "error");
    });
  });

  // Back button
  backButton.addEventListener("click", () => {
    window.location.href = "/ctf";
  });

  function showResponse(message, type) {
    responseText.textContent = message;
    responseBox.className = `response-box response-${type}`;
    responseBox.style.display = "flex";
    
    // Hide after 5 seconds
    setTimeout(() => {
      responseBox.style.display = "none";
    }, 5000);
  }
});

// Helper to read cookies (for authentication)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}