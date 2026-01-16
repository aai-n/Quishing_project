function analyzeQR() {
    const fileInput = document.getElementById("qrInput");
    const resultDiv = document.getElementById("result");

    if (!fileInput.files.length) {
        resultDiv.textContent = "Please upload a QR image.";
        resultDiv.className = "error";
        resultDiv.classList.remove("hidden");
        return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    resultDiv.textContent = "Analyzing...";
    resultDiv.className = "";
    resultDiv.classList.remove("hidden");

    fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.fraud === true) {
            resultDiv.textContent = "🚨 POTENTIAL QUISHING DETECTED";
            resultDiv.className = "error";
        } else {
            resultDiv.textContent = "✅ SAFE QR CODE";
            resultDiv.className = "safe";
        }
    })
    .catch(() => {
        resultDiv.textContent = "Server error. Is backend running?";
        resultDiv.className = "error";
    });
}
