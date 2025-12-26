let qr = null;
let scanning = false;

function initLocationQR() {
  qr = new Html5Qrcode("reader");
}

function parseLocation(raw) {
  if (!raw) return null;
  const text = raw.trim();

  // JSON
  if (text.startsWith("{")) {
    try {
      const obj = JSON.parse(text);
      if (obj.type === "LOCATION" && obj.location_code) {
        return obj.location_code;
      }
    } catch {}
  }

  // LOCATION|D01-01
  if (text.includes("|")) {
    const parts = text.split("|");
    if (parts[0].toUpperCase() === "LOCATION") {
      return parts[1];
    }
  }

  // plain
  return text;
}

async function loadInventory(location) {
  document.getElementById("locationText").innerText = location;

  const res = await fetch(`/api/inventory?location_code=${encodeURIComponent(location)}`);
  const data = await res.json();

  const tbody = document.querySelector("#invTable tbody");
  tbody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = "<tr><td colspan='6'>재고 없음</td></tr>";
    return;
  }

  data.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.item_code}</td>
      <td>${r.item_name}</td>
      <td>${r.brand}</td>
      <td>${r.spec}</td>
      <td>${r.lot}</td>
      <td style="text-align:right">${r.quantity}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function onScan(text) {
  if (!scanning) return;
  scanning = false;
  await qr.stop();

  const loc = parseLocation(text);
  if (loc) loadInventory(loc);
}

async function startScan() {
  if (scanning) return;
  scanning = true;

  await qr.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 250 },
    onScan,
    () => {}
  );
}

async function stopScan() {
  scanning = false;
  try { await qr.stop(); } catch {}
}

function manualApply() {
  const loc = document.getElementById("manual").value;
  if (loc) loadInventory(loc);
}
