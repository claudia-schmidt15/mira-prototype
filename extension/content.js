(() => {
  console.log("🟣 Mira content.js loaded (URL parsing mode)");

  if (window.__MIRA_LOADED__) {
    console.log("⚠️ Mira already loaded");
    return;
  }
  window.__MIRA_LOADED__ = true;

  // ======================================================
  // Utils — URL parsing
  // ======================================================
  function parseGoogleMapsRouteFromURL() {
  const url = decodeURIComponent(window.location.href);

  if (!url.includes("/maps/dir/")) {
    console.warn("❌ Mira: Not a directions URL");
    return null;
  }

  // ---------------------------
  // START (from /dir/)
  // ---------------------------
  const dirPart = url.split("/maps/dir/")[1];
  const parts = dirPart.split("/");

  function parseLatLng(str) {
    const match = str.match(/(-?\d+\.\d+),(-?\d+\.\d+)/);
    if (!match) return null;
    return {
      lat: parseFloat(match[1]),
      lng: parseFloat(match[2])
    };
  }

  const start = parseLatLng(parts[0]);
  if (!start) {
    console.warn("❌ Mira: Could not parse start");
    return null;
  }

  // ---------------------------
  // END (path OR data section)
  // ---------------------------
  let end = parseLatLng(parts[1]);

  if (!end) {
    // Fallback: extract from !1d{lng}!2d{lat}
    const match = url.match(/!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)/);
    if (match) {
      end = {
        lng: parseFloat(match[1]),
        lat: parseFloat(match[2])
      };
    }
  }

  if (!end) {
    console.warn("❌ Mira: Could not parse end");
    return null;
  }

  return { start, end };
}


  // ======================================================
  // UI — Mira panel
  // ======================================================
  const panel = document.createElement("div");
  panel.style.cssText = `
    position: fixed;
    top: 100px;
    right: 20px;
    width: 240px;
    padding: 14px;
    background: #ffd1dc;
    border-radius: 14px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    font-family: Arial, sans-serif;
    z-index: 9999;
  `;

  const title = document.createElement("div");
  title.innerText = "Mira";
  title.style.fontWeight = "bold";
  title.style.fontSize = "16px";

  const status = document.createElement("div");
  status.innerText = "Ready to analyze";
  status.style.margin = "8px 0";
  status.style.fontSize = "13px";

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
  console.log("📍 Full URL:", window.location.href);

  status.innerText = "Parsing route from URL…";

  const route = parseGoogleMapsRouteFromURL();

  if (!route) {
    status.innerText = "Could not parse route";
    return;
  }

  status.innerText = "Requesting safer route…";

  const res = await fetch(
    `http://127.0.0.1:8000/route?` +
    `start_lat=${route.start.lat}` +
    `&start_lng=${route.start.lng}` +
    `&end_lat=${route.end.lat}` +
    `&end_lng=${route.end.lng}` +
    `&safety_weight=0.7`
  );

  if (!res.ok) {
    status.innerText = "Route request failed";
    console.error(await res.text());
    return;
  }

  const geojson = await res.json();
  console.log("🟣 Mira route GeoJSON:", geojson);

  status.innerText = "Route received ✓";
};
    panel.append(title, status, button);
    document.body.appendChild(panel);
})();
