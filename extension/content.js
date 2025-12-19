console.log("Mira loaded");

// ===============================
// Create Mira panel
// ===============================
const panel = document.createElement("div");
panel.style.position = "fixed";
panel.style.top = "100px";
panel.style.right = "20px";
panel.style.background = "#ffd1dc";
panel.style.color = "#000";
panel.style.padding = "14px";
panel.style.borderRadius = "14px";
panel.style.fontFamily = "Arial, sans-serif";
panel.style.boxShadow = "0 4px 10px rgba(0,0,0,0.15)";
panel.style.zIndex = "9999";
panel.style.width = "200px";

// ===============================
// Title
// ===============================
const title = document.createElement("div");
title.innerText = "Mira";
title.style.fontWeight = "bold";
title.style.fontSize = "16px";
title.style.marginBottom = "8px";
panel.appendChild(title);

// ===============================
// Status text
// ===============================
const status = document.createElement("div");
status.innerText = "Ready to analyze";
status.style.fontSize = "13px";
status.style.marginBottom = "12px";
panel.appendChild(status);

// ===============================
// Analyze Route button
// ===============================
const button = document.createElement("button");
button.innerText = "Analyze Route";
button.style.width = "100%";
button.style.padding = "8px";
button.style.border = "none";
button.style.borderRadius = "8px";
button.style.background = "#ff69b4";
button.style.color = "white";
button.style.fontSize = "14px";
button.style.cursor = "pointer";

// ===============================
// Button click handler
// ===============================
button.onclick = async () => {
  status.innerText = "Analyzing…";

  try {
    const response = await fetch("http://127.0.0.1:8000/score/route", {
      method: "POST"
    });

    const data = await response.json();
    status.innerText = `NYC: ${data.label} (${data.score})`;
  } catch (err) {
    console.error("Mira API error:", err);
    status.innerText = "Error contacting Mira API";
  }
};

panel.appendChild(button);

// ===============================
// Inject panel into page
// ===============================
document.body.appendChild(panel);

