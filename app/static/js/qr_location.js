let qr = null;
let scanning = false;

// ================================
// INIT
// ================================
function initLocationQR() {
  qr = new Html5Qrcode("reader");

  // 모바일에서만 자동 시작
  if (/Mobi|Android/i.test(navigator.userAgent)) {
    startScan();
  }
}

// ================================
// QR PARSER (STEP 3 표준)
// ================================
function parseLocationQR(raw) {
  if (!raw) return null;

  // JSON QR
  if (raw.startsWith("{")) {
    try {
      const obj = JSON.parse(raw);
      if (obj.type === "LOCATION" && obj.location_code) {
        return obj.location_code;
      }
    } catch (e) {}
  }

  // fallback (단순 텍스트)
  return raw.trim();
}

// ================================
// INVENTORY LOAD
// ================================
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

// ================================
// SCAN HANDLER
// ================================
async function onScanSuccess(text) {
  if (!scanning) return;

  scanning = false;
  await qr.stop();

  const location = parseLocationQR(text);
  if (location) loadInventory(location);
}

// ================================
// CONTROL
// ================================
async function startScan() {
  if (scanning) return;
  scanning = true;

  await qr.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 250 },
    onScanSuccess,
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
