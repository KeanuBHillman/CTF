document.addEventListener("DOMContentLoaded", () => {
  const TEAM_SIZE = 2; // 🔧 set number of required S numbers here

  const teamnameInput = document.getElementById("teamname");
  const snumberFieldsDiv = document.getElementById("snumber-fields");
  const createBtn = document.getElementById("create-btn");
  const responseBox = document.getElementById("response-box");
  const responseText = document.getElementById("response-text");

  // Dynamically create S number fields (first = Your S Number, rest = Extra Members)
  for (let i = 0; i < TEAM_SIZE; i++) {
    const wrapper = document.createElement("div");
    wrapper.className = "form-group";

    const input = document.createElement("input");
    input.type = "text";
    input.id = `snumber-${i}`;

    if (i === 0) {
      input.placeholder = "YOUR S NUMBER";
    } else {
      input.placeholder = "EXTRA MEMBER S NUMBER";
    }

    wrapper.appendChild(input);
    snumberFieldsDiv.appendChild(wrapper);
  }

  createBtn.addEventListener("click", () => {
    const teamname = teamnameInput.value.trim();
    const snumbers = [];

    for (let i = 0; i < TEAM_SIZE; i++) {
      const val = document.getElementById(`snumber-${i}`).value.trim();
      if (val) snumbers.push(val); // only push non-empty values
    }

    // Reset response box
    responseBox.style.display = "none";
    responseBox.className = "response-box";

    // Validation
    if (!teamname) {
      responseText.textContent = "Team name is required";
      responseBox.classList.add("response-error");
      responseBox.style.display = "flex";
      return;
    }

    // Check only the first S number field
    const yourSnumber = document.getElementById("snumber-0").value.trim();
    if (!yourSnumber) {
      responseText.textContent = "Your S Number is required";
      responseBox.classList.add("response-error");
      responseBox.style.display = "flex";
      return;
    }

    // Send request
    fetch("/api/create_team", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ teamname, snumbers }),
    })
      .then(async (res) => {
        const result = await res.json();
        responseText.textContent = result.message || "No response message";

        if (res.status === 200) {
          responseBox.classList.add("response-success");
          responseBox.style.display = "flex";

          // ✅ Redirect after short delay so user sees success
          setTimeout(() => {
            window.location.href = "/ctf";
          }, 1000);
        } else {
          responseBox.classList.add("response-error");
          responseBox.style.display = "flex";
        }
      })
      .catch((err) => {
        responseText.textContent = "Server error, please try again.";
        responseBox.classList.add("response-error");
        responseBox.style.display = "flex";
        console.error("Error creating team:", err);
      });
  });
});
