function askHelperAI() {
    const question = document.getElementById("helperInput").value;

    fetch("/ask_helper_ai", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ question })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("helperResponse").innerText = data.answer;
    })
    .catch(() => {
        document.getElementById("helperResponse").innerText =
            "Something went wrong. Please try again.";
    });
}
