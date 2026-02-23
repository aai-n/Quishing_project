async function analyzeQR() {
    const input = document.getElementById("qrInput");
    if (!input.files.length) return alert("Select an image");

    const file = input.files[0];
    const formData = new FormData();
    formData.append("image", file);

    const resultDiv = document.getElementById("result");

    try {
        const res = await fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        resultDiv.classList.remove("hidden");
        resultDiv.innerHTML = `
            <p><strong>Decoded Data:</strong> ${data.decoded_data}</p>
            <p><strong>Fraud:</strong> ${data.fraud}</p>
            <p><strong>Confidence:</strong> ${data.confidence}</p>
            <p><strong>Reason:</strong> ${data.reason}</p>
        `;
    } catch (err) {
        alert("Error analyzing QR");
        console.error(err);
    }
}