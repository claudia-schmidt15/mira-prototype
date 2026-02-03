(() => {
  console.log("🔥 MIRA CONTENT SCRIPT STARTED");

  if (window.__MIRA_LOADED__) {
    console.log("⚠️ Mira already loaded");
    return;
  }
  window.__MIRA_LOADED__ = true;

  console.log("🟣 Mira loaded");

  // ======================================================
  // Canvas overlay
  // ======================================================
  let miraCanvas = document.getElementById("mira-canvas");
  let ctx;

  function initCanvas() {
  if (miraCanvas) return;

  const svg = document.querySelector("svg");
  if (!svg) {
    console.warn("❌ Mira: SVG not found for canvas attach");
    return;
  }

  const container = svg.parentElement;
  if (!container) {
    console.warn("❌ Mira: SVG parent not found");
    return;
  }

  miraCanvas = document.createElement("canvas");
  miraCanvas.id = "mira-canvas";

  miraCanvas.style.position = "absolute";
  miraCanvas.style.top = "0";
  miraCanvas.style.left = "0";
  miraCanvas.style.pointerEvents = "none";
  miraCanvas.style.zIndex = "999999";

  container.style.position = "relative";
  container.appendChild(miraCanvas);

  ctx = miraCanvas.getContext("2d");
  resizeCanvas();

  console.log("🟣 Mira canvas attached INSIDE map container");
}


  function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const rect = miraCanvas.parentElement.getBoundingClientRect();

  miraCanvas.width = rect.width * dpr;
  miraCanvas.height = rect.height * dpr;

  miraCanvas.style.width = rect.width + "px";
  miraCanvas.style.height = rect.height + "px";

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}


  window.addEventListener("resize", resizeCanvas);
  initCanvas();

  // ======================================================
  // Utils
  // ======================================================
  function labelToColor(label) {
    if (label === "comfortable" || label === "mostly safe") return "#22c55e";
    if (label === "mixed") return "#facc15";
    return "#ef4444";
  }

  // ======================================================
  // Find the REAL Google route path
  // ======================================================
  function getGoogleRoutePathElement() {
    const paths = document.querySelectorAll("svg path");
    let best = null;
    let maxLen = 0;

    paths.forEach(p => {
      try {
        const len = p.getTotalLength();
        if (len > maxLen) {
          maxLen = len;
          best = p;
        }
      } catch {}
    });

    return best;
  }

  // ======================================================
  // Convert Google SVG path → screen points
  // ======================================================
  function densifyRouteToScreen(pathEl, spacing = 8) {
    const svg = pathEl.ownerSVGElement;
    const ctm = pathEl.getScreenCTM();
    if (!svg || !ctm) return [];

    const total = pathEl.getTotalLength();
    const pts = [];
    const svgPoint = svg.createSVGPoint();

    for (let d = 0; d <= total; d += spacing) {
      const p = pathEl.getPointAtLength(d);
      svgPoint.x = p.x;
      svgPoint.y = p.y;
      const screen = svgPoint.matrixTransform(ctm);
      pts.push({ x: screen.x, y: screen.y });
    }

    return pts;
  }

  // ======================================================
  // Draw canvas route (this bypasses Google DOM entirely)
  // ======================================================
  function drawCanvasRoute(points, color) {
    if (points.length < 2) return;

    ctx.clearRect(0, 0, miraCanvas.width, miraCanvas.height);

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }

    ctx.strokeStyle = "rgba(255, 0, 0, 1)"; // 🔴 bright red
    ctx.lineWidth = 16;
    ctx.globalAlpha = 1;
    ctx.shadowColor = "rgba(255,0,0,0.6)";
    ctx.shadowBlur = 12;
    ctx.stroke();

    console.log("🟣 Mira canvas route drawn");
  }

  // ======================================================
  // UI
  // ======================================================
  const panel = document.createElement("div");
  panel.style.cssText = `
    position: fixed;
    top: 100px;
    right: 20px;
    width: 220px;
    padding: 14px;
    background: #ffd1dc;
    border-radius: 14px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    font-family: Arial;
    z-index: 9999;
  `;

  const title = document.createElement("div");
  title.innerText = "Mira";
  title.style.fontWeight = "bold";
  title.style.fontSize = "16px";

  const status = document.createElement("div");
  status.innerText = "Ready to analyze";
  status.style.margin = "8px 0";

  const button = document.createElement("button");
  button.innerText = "Analyze Route";
  button.style.cssText = `
    width: 100%;
    padding: 8px;
    border-radius: 8px;
    border: none;
    background: #ff69b4;
    color: white;
    font-size: 14px;
    cursor: pointer;
  `;

  button.onclick = async () => {
    status.innerText = "Analyzing route…";

    const routePath = getGoogleRoutePathElement();
    if (!routePath) {
      status.innerText = "No route found";
      console.warn("❌ Mira: route not found");
      return;
    }

    const screenPoints = densifyRouteToScreen(routePath);

    const res = await fetch("http://127.0.0.1:8000/route/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        points: screenPoints,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      })
    });

    const data = await res.json();
    const label = data.label || "mixed";
    const color = labelToColor(label);

    drawCanvasRoute(screenPoints, color);
    status.innerText = `Route analyzed ✓ (${label})`;
  };

  panel.append(title, status, button);
  document.body.appendChild(panel);
})();
