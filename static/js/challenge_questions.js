document.addEventListener("DOMContentLoaded", () => {
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
        if (data.length === 0) {
          // Fallback to default questions if none exist in database
          questions = [
            {
              id: 1,
              question_text: "What is the main technology used in this challenge?",
              question_type: "text",
              required: true,
              points: 75,
              order: 1
            },
            {
              id: 2,
              question_text: "What vulnerability did you identify?",
              question_type: "textarea",
              required: true,
              points: 150,
              order: 2
            },
            {
              id: 3,
              question_text: "How would you fix this vulnerability?",
              question_type: "textarea",
              required: false,
              points: 75,
              order: 3
            }
          ];
        } else {
          // Use questions from database
          questions = data;
        }
        renderQuestions();
      })
      .catch(error => {
        console.error("Error loading questions:", error);
        // Fallback to default questions on error
        questions = [
          {
            id: 1,
            question_text: "What is the main technology used in this challenge?",
            question_type: "text",
            required: true,
            points: 75,
            order: 1
          },
          {
            id: 2,
            question_text: "What vulnerability did you identify?",
            question_type: "textarea",
            required: true,
            points: 150,
            order: 2
          }
        ];
        renderQuestions();
      });
  }

  function renderQuestions() {
    const totalPoints = questions.reduce((sum, q) => sum + (q.points || 0), 0);
    
    // Update challenge points with breakdown
    if (challengePoints && totalPoints > 0) {
      challengePoints.innerHTML = `<strong>${totalPoints} points</strong> <small>(${questions.length} questions)</small>`;
    }
    
    questionsList.innerHTML = questions.map((q, index) => `
      <div class="question-item">
        <label class="question-label">
          ${index + 1}. ${q.question_text} 
          ${q.required ? '<span class="required">*</span>' : ''}
          <span class="question-points">${q.points || 10} pts</span>
        </label>
        ${q.question_type === 'textarea' 
          ? `<textarea id="question-${q.id}" rows="4" placeholder="Your answer..."></textarea>`
          : `<input type="text" id="question-${q.id}" placeholder="Your answer..." />`
        }
      </div>
    `).join('');
  }

  // Submit answers
  submitButton.addEventListener("click", () => {
    const answers = {};
    let hasError = false;

    // Collect answers
    questions.forEach(q => {
      const input = document.getElementById(`question-${q.id}`);
      const value = input.value.trim();
      
      if (q.required && !value) {
        input.style.borderColor = "red";
        hasError = true;
      } else {
        input.style.borderColor = "";
        answers[q.id] = value;
      }
    });

    if (hasError) {
      showResponse("Please answer all required questions.", "error");
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
        let message = `🎉 Submission complete!\n`;
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
          document.getElementById(`question-${q.id}`).value = "";
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