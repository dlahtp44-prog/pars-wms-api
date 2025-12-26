let qr = null;
let scanning = false;

let itemCode = null;
let lot = null;
let locationCode = null;

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

  loadLocations();
}

// ================================
// LOAD LOCATIONS
// ================================
async function loadLocations() {
  const res = await fetch(`/api/inventory?item_code=${itemCode}&lot=${lot}`);
  const data = await res.json();

  const tbody = document.querySelector("#locTable tbody");
  tbody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = "<tr><td colspan='4'>출고 가능한 재고 없음</td></tr>";
    return;
  }

  data.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <input type="radio" name="loc" value="${r.location_code}">
      </td>
      <td>${r.location_code}</td>
      <td>${r.lot}</td>
      <td style="text-align:right">${r.quantity}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ================================
// OUTBOUND
// ================================
async function submitOutbound() {
  const checked = document.querySelector("input[name='loc']:checked");
  if (!checked) {
    alert("출고할 로케이션을 선택하세요.");
    return;
  }

  locationCode = checked.value;

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
      location_code: locationCode,
      quantity: qty
    })
  });

  if (res.ok) {
    alert(`출고 완료 (${locationCode}, 수량 ${qty})`);
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
  locationCode = null;

  document.getElementById("itemInfo").innerText = "-";
  document.querySelector("#locTable tbody").innerHTML = "";
  document.getElementById("qty").value = 1;
}
