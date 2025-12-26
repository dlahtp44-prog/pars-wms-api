let qr = null;
let scanning = false;

let itemCode = null;
let lot = null;

// ================================
// INIT
// ================================
function initOutboundQR() {
  qr = new Html5Qrcode("reader");
  startScan();
}

// ================================
// QR PARSER
// ================================
function parseQR(raw) {
  if (!raw) return null;
  if (raw.startsWith("{")) {
    try {
      return JSON.parse(raw);
    } catch {}
  }
  return null;
}

// ================================
// SCAN FLOW
// ================================
async function onScan(text) {
  if (!scanning) return;

  const data = parseQR(text);
  if (!data || data.type !== "ITEM") return;

  itemCode = data.item_code;
  lot = data.lot;

  document.getElementById("itemInfo").innerText =
    `${itemCode} / LOT ${lot}`;

  scanning = false;
  await qr.stop();
}

// ================================
// OUTBOUND API
// ================================
async function submitOutbound() {
  if (!itemCode || !lot) {
    alert("상품 QR을 먼저 스캔하세요.");
    return;
  }

  const qty = parseInt(document.getElementById("qty").value, 10);
  if (!qty || qty < 1) {
    alert("수량은 1 이상이어야 합니다.");
    return;
  }

  const res = await fetch("/api/outbound", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      item_code: itemCode,
      lot: lot,
      quantity: qty
    })
  });

  if (res.ok) {
    alert(`출고 완료 (수량 ${qty})`);
    resetAll();
    startScan();
  } else {
    const err = await res.json();
    alert(err.error || "출고 실패");
  }
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
    onScan,
    () => {}
  );
}

async function stopScan() {
  scanning = false;
  try { await qr.stop(); } catch {}
}

function resetAll() {
  itemCode = null;
  lot = null;
  document.getElementById("itemInfo").innerText = "-";
  document.getElementById("qty").value = 1;
}
