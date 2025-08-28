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
    fetch("/api/join_team", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ snumber, teamname }),
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
        console.error("Error joining team:", err);
      });
  });
});
