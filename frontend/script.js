function analyzeQR() {
    const input = document.getElementById("qrInput");
    const result = document.getElementById("result");

    if (!input.files.length) {
        result.textContent = "Please upload a QR image.";
        result.className = "error";
        result.classList.remove("hidden");
        return;
    }

    const formData = new FormData();
    formData.append("image", input.files[0]);

    result.textContent = "Analyzing...";
    result.className = "";
    result.classList.remove("hidden");

    fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.fraud) {
            result.textContent = `🚨 FRAUD (${data.confidence}) — ${data.reason}`;
            result.className = "error";
        } else {
            result.textContent = `✅ SAFE (${data.confidence}) — ${data.reason}`;
            result.className = "safe";
        }
    })
    .catch(() => {
        result.textContent = "Backend not running";
        result.className = "error";
    });
}
