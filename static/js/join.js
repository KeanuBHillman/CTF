document.addEventListener("DOMContentLoaded", () => {
  const snumberInput = document.getElementById("snumber");
  const teamnameInput = document.getElementById("teamname");
  const joinBtn = document.getElementById("join-btn");
  const responseBox = document.getElementById("response-box");
  const responseText = document.getElementById("response-text");
  joinBtn.addEventListener("click", () => {
    const snumber = snumberInput.value.trim();
    const teamname = teamnameInput.value.trim();
    // Reset response box
    responseBox.style.display = "none";
    responseBox.className = "response-box";
    // Validation
    if (!snumber || !teamname) {
      responseText.textContent = "Missing fields";
      responseBox.classList.add("response-error");
      responseBox.style.display = "flex";
      return;
    }
    // Send request
    fetch("/api/teams/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team_name: teamname, member_name: snumber }), // changed: was { snumber, teamname }
    })
      .then(async (res) => {
        const result = await res.json();
        responseText.textContent =
          result.message || result.detail || "No response message";
        if (res.status === 200) {
          responseBox.classList.add("response-success");
          responseBox.style.display = "flex";
          //  Redirect after short delay
          setTimeout(() => {
            window.location.href = "/ctf";
          }, 500);
        } else {
          responseBox.classList.add("response-error");
          responseBox.style.display = "flex";
        }
      })
      .catch((err) => {
        responseText.textContent = "Server error, please try again.";
        responseBox.classList.add("response-error");
        responseBox.style.display = "flex";
        console.error("Error joining team:", err);
      });
  });
});
