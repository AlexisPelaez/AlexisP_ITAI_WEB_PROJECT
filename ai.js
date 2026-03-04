function askAI() {
    const userMessage = document.getElementById("aiInput").value;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("aiResponse").textContent = data.response;
    })
    .catch(err => {
        document.getElementById("aiResponse").textContent = "Error contacting AI.";
    });
}