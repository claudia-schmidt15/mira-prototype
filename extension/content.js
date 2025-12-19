console.log("Mira loaded");

function getRouteColor(score) {
  if (score >= 70) return "#00aa66";   // green
  if (score >= 40) return "#f4c430";   // yellow
  return "#d9534f";                    // red
}

function drawFakeRoute(score) {
  // Remove existing route if it exists
  const existing = document.getElementById("mira-route");
  if (existing) existing.remove();

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("id", "mira-route");
  svg.style.position = "fixed";
  svg.style.top = "0";
  svg.style.left = "0";
  svg.style.width = "100vw";
  svg.style.height = "100vh";
  svg.style.pointerEvents = "none";
  svg.style.zIndex = "9998";

  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", "300");
  line.setAttribute("y1", "300");
  line.setAttribute("x2", "600");
  line.setAttribute("y2", "500");
  line.setAttribute("stroke", getRouteColor(score));
  line.setAttribute("stroke-width", "6");
  line.setAttribute("stroke-linecap", "round");

  svg.appendChild(line);
  document.body.appendChild(svg);
}

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
drawFakeRoute(data.score);

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

