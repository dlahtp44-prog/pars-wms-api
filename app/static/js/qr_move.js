let qr = null;
let scanning = false;

// 이동 상태
let fromLocation = null;
let toLocation = null;
let itemCode = null;
let lot = null;

// ================================
// INIT
// ================================
function initMoveQR() {
  qr = new Html5Qrcode("reader");
  startScan();
}

// ================================
// QR PARSER (STEP 3 표준)
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
  if (!data || !data.type) return;

  // 1️⃣ 출발지
  if (data.type === "LOCATION" && !fromLocation) {
    fromLocation = data.location_code;
    document.getElementById("fromLoc").innerText = fromLocation;
    return;
  }

  // 2️⃣ 상품
  if (data.type === "ITEM" && fromLocation && !itemCode) {
    itemCode = data.item_code;
    lot = data.lot;
    document.getElementById("itemInfo").innerText =
      `${itemCode} / LOT ${lot}`;
    return;
  }

  // 3️⃣ 도착지 → 이동 실행
  if (data.type === "LOCATION" && fromLocation && itemCode && !toLocation) {
    toLocation = data.location_code;
    document.getElementById("toLoc").innerText = toLocation;
    await submitMove();
  }
}

// ================================
// MOVE API
// ================================
async function submitMove() {
  scanning = false;
  await qr.stop();

  const qty = parseInt(document.getElementById("qty").value, 10);

  if (!qty || qty < 1) {
    alert("수량은 1 이상이어야 합니다.");
    startScan();
    return;
  }

  const res = await fetch("/api/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      item_code: itemCode,
      lot: lot,
      from_location: fromLocation,
      to_location: toLocation,
      quantity: qty
    })
  });

  if (res.ok) {
    alert(`이동 완료 (수량 ${qty})`);
    resetAll();
    startScan();
  } else {
    const err = await res.json();
    alert(err.error || "이동 실패");
    startScan();
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
  fromLocation = null;
  toLocation = null;
  itemCode = null;
  lot = null;

  document.getElementById("fromLoc").innerText = "-";
  document.getElementById("itemInfo").innerText = "-";
  document.getElementById("toLoc").innerText = "-";
  document.getElementById("qty").value = 1;
}
