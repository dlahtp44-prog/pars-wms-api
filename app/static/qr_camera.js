let qrScanner = null;
let moveState = {
  from: null,
  item: null,
  qty: null
};

/* QR 처리 */
function processQR(text) {
  const params = new URLSearchParams(text);
  const warehouse = params.get("warehouse") || "MAIN";
  const location = params.get("location");
  const item_code = params.get("item_code");
  const lot_no = params.get("lot_no");

  /* 1️⃣ 출발 로케이션 */
  if (location && !moveState.from) {
    moveState.from = { warehouse, location };
    document.getElementById("msg").innerText =
      `📍 출발지 설정됨: ${location}\n이동할 제품 선택`;
    loadLocationItems(warehouse, location);
    return;
  }

  /* 2️⃣ 목적 로케이션 */
  if (location && moveState.from && moveState.item) {
    executeMove(warehouse, location);
    return;
  }

  alert("❌ 처리할 수 없는 QR");
}

/* 출발 로케이션 재고 조회 */
async function loadLocationItems(warehouse, location) {
  const res = await fetch(
    `/api/inventory?warehouse=${warehouse}&location=${location}`
  );
  const rows = await res.json();

  let html = "<h3>📦 이동할 제품 선택</h3>";
  rows.forEach(r => {
    html += `
      <div style="margin-bottom:6px">
        <b>${r.item_code}</b> (${r.lot_no}) / 수량 ${r.qty}
        <button onclick="selectItem('${r.item_code}','${r.lot_no}',${r.qty})">
          선택
        </button>
      </div>
    `;
  });

  document.getElementById("result").innerHTML = html;
}

/* 제품 선택 */
function selectItem(item_code, lot_no, maxQty) {
  const qty = prompt(`이동 수량 입력 (최대 ${maxQty})`);
  if (!qty || Number(qty) <= 0) return;

  moveState.item = { item_code, lot_no };
  moveState.qty = Number(qty);

  document.getElementById("msg").innerText =
    `📦 선택됨: ${item_code} / ${qty}개\n👉 목적 로케이션 QR 스캔`;
}

/* 이동 실행 */
async function executeMove(toWarehouse, toLocation) {
  const body = {
    warehouse: moveState.from.warehouse,
    from_location: moveState.from.location,
    to_location: toLocation,
    item_code: moveState.item.item_code,
    lot_no: moveState.item.lot_no,
    qty: moveState.qty
  };

  const res = await fetch("/api/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (res.ok) {
    alert("✅ 이동 완료");
    moveState = { from: null, item: null, qty: null };
    document.getElementById("result").innerHTML = "";
    document.getElementById("msg").innerText = "📷 다음 작업 가능";
  } else {
    alert("❌ 이동 실패");
  }
}
