// ==================================================
// QR MOVE (FROM -> ITEM -> QTY -> TO => AUTO MOVE)
// ==================================================

let html5Qr = null;
let currentCameraId = null;
let cameraIds = [];
let scanning = false;

// 현재 작업 상태
const state = {
  from: "",
  item_code: "",
  lot: "",
  to: ""
};

// ------------------------------
// UI helpers
// ------------------------------
function setText(id, value) {
  document.getElementById(id).innerText = value || "-";
}

function showMsg(type, text) {
  const el = document.getElementById("msg");
  if (!text) {
    el.innerHTML = "";
    return;
  }
  if (type === "ok") el.innerHTML = `<div class="ok">${text}</div>`;
  else el.innerHTML = `<div class="err">${text}</div>`;
}

function refreshUI() {
  setText("fromLoc", state.from);
  setText("itemCode", state.item_code);
  setText("lot", state.lot);
  setText("toLoc", state.to);
}

// ------------------------------
// QR content parser
// 지원:
// 1) JSON: {"type":"LOCATION","location_code":"D01-01"}
// 2) TEXT: LOCATION|D01-01
// 3) TEXT: D01-01  (로케이션으로 간주)
// 4) JSON: {"type":"ITEM","item_code":"728750","lot":"H01"}
// 5) TEXT: ITEM|728750|H01
// 6) TEXT: 728750|H01 (상품으로 간주)
// ------------------------------
function parseQr(raw) {
  if (!raw) return null;

  const text = ("" + raw).trim();

  // JSON 우선
  if (text.startsWith("{") && text.endsWith("}")) {
    try {
      const obj = JSON.parse(text);
      if (obj.type === "LOCATION" && obj.location_code) {
        return { kind: "LOCATION", location_code: String(obj.location_code).trim() };
      }
      if (obj.type === "ITEM" && obj.item_code && obj.lot) {
        return {
          kind: "ITEM",
          item_code: String(obj.item_code).trim(),
          lot: String(obj.lot).trim()
        };
      }
    } catch (e) {
      // JSON 파싱 실패 -> 아래 텍스트 파서로 진행
    }
  }

  // 파이프 텍스트
  if (text.includes("|")) {
    const parts = text.split("|").map(p => p.trim()).filter(Boolean);

    // LOCATION|D01-01
    if (parts.length === 2 && parts[0].toUpperCase() === "LOCATION") {
      return { kind: "LOCATION", location_code: parts[1] };
    }

    // ITEM|728750|H01
    if (parts.length >= 3 && parts[0].toUpperCase() === "ITEM") {
      return { kind: "ITEM", item_code: parts[1], lot: parts[2] };
    }

    // 728750|H01
    if (parts.length === 2) {
      // 상품으로 간주
      return { kind: "ITEM", item_code: parts[0], lot: parts[1] };
    }
  }

  // 단일 텍스트인 경우:
  // - 이미 from 세팅 안 됐으면 로케이션으로 간주
  // - from 있고 item 없으면 "품번"만 들어온 걸로 볼 수도 있지만 lot가 없어서 불가
  // => 여기서는 "로케이션"으로 처리 (현장에서는 로케이션 QR이 더 흔함)
  return { kind: "LOCATION", location_code: text };
}

// ------------------------------
// Scan flow apply
// ------------------------------
async function applyParsed(parsed) {
  if (!parsed) return;

  // 1) FROM이 비어있으면 LOCATION은 무조건 FROM
  if (!state.from && parsed.kind === "LOCATION") {
    state.from = parsed.location_code;
    showMsg("ok", `출발지(FROM) 설정: ${state.from}`);
    refreshUI();
    return;
  }

  // 2) FROM이 있고, ITEM이 비어있으면 ITEM을 받는다
  if (state.from && !state.item_code && parsed.kind === "ITEM") {
    state.item_code = parsed.item_code;
    state.lot = parsed.lot;
    showMsg("ok", `상품 설정: 품번 ${state.item_code}, LOT ${state.lot}`);
    refreshUI();
    return;
  }

  // 3) FROM+ITEM이 있고, TO가 비어있으면 LOCATION은 TO로 받는다
  if (state.from && state.item_code && !state.to && parsed.kind === "LOCATION") {
    state.to = parsed.location_code;
    showMsg("ok", `도착지(TO) 설정: ${state.to} → 이동 처리 시도`);
    refreshUI();

    // 자동 처리
    await submitMove();
    return;
  }

  // 그 외는 안내
  if (parsed.kind === "LOCATION") {
    showMsg("err", `로케이션 QR 감지(${parsed.location_code}) 했지만 현재 단계와 맞지 않습니다. (FROM→ITEM→TO 순서 확인)`);
  } else {
    showMsg("err", `상품 QR 감지(품번 ${parsed.item_code}, LOT ${parsed.lot}) 했지만 현재 단계와 맞지 않습니다. (FROM→ITEM→TO 순서 확인)`);
  }
}

// ------------------------------
// Submit move (uses existing /api/move Form API)
// ------------------------------
async function submitMove() {
  const qty = parseInt(document.getElementById("qty").value, 10);

  if (!state.from) return showMsg("err", "출발지(FROM) 로케이션을 먼저 스캔하세요.");
  if (!state.item_code || !state.lot) return showMsg("err", "상품 QR(품번+LOT)을 먼저 스캔하세요.");
  if (!qty || qty <= 0) return showMsg("err", "수량을 1 이상으로 입력하세요.");
  if (!state.to) return showMsg("err", "도착지(TO) 로케이션을 스캔하세요.");
  if (state.from === state.to) return showMsg("err", "출발지와 도착지가 같습니다. 다른 TO를 스캔하세요.");

  try {
    // 기존 서버가 Form(...) 으로 받으므로 form-urlencoded로 전송
    const body = new URLSearchParams();
    body.append("item_code", state.item_code);
    body.append("lot", state.lot);
    body.append("location_from", state.from);
    body.append("location_to", state.to);
    body.append("quantity", String(qty));

    const res = await fetch("/api/move", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString()
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const msg = data.error || "이동 처리 실패";
      showMsg("err", msg);
      return;
    }

    showMsg("ok", `이동 완료 ✅  ${state.from} → ${state.to} / 품번 ${state.item_code} / LOT ${state.lot} / 수량 ${qty}`);

    // 다음 작업을 위해 TO만 비우고(연속 이동 가능) 또는 전체 초기화
    // 여기서는 전체 초기화(안전)
    state.from = "";
    state.item_code = "";
    state.lot = "";
    state.to = "";
    document.getElementById("qty").value = 1;
    refreshUI();

  } catch (e) {
    showMsg("err", `네트워크/서버 오류: ${e}`);
  }
}

// 수동 버튼용
async function qrMoveSubmitManual() {
  await submitMove();
}

// ------------------------------
// Camera control
// ------------------------------
async function qrMoveInit() {
  refreshUI();
  showMsg("", "");

  html5Qr = new Html5Qrcode("reader");

  // 카메라 목록 가져오기
  const devices = await Html5Qrcode.getCameras().catch(() => []);
  cameraIds = (devices || []).map(d => d.id);

  // 후면 우선 선택(가능한 경우)
  // getCameras 결과에 label은 권한 전에는 비어 있을 수 있음
  currentCameraId = cameraIds[0] || null;

  // 자동 시작은 안 함 (현장에서는 버튼 시작 선호)
}

async function qrMoveStart() {
  if (!html5Qr) return;
  if (scanning) return;

  showMsg("", "");

  const config = {
    fps: 10,
    qrbox: { width: 260, height: 260 },
    disableFlip: true
  };

  // 카메라 ID가 없으면 facingMode로 시도
  try {
    scanning = true;
    if (currentCameraId) {
      await html5Qr.start(
        { deviceId: { exact: currentCameraId } },
        config,
        (decodedText) => onScan(decodedText),
        () => {}
      );
    } else {
      await html5Qr.start(
        { facingMode: "environment" },
        config,
        (decodedText) => onScan(decodedText),
        () => {}
      );
    }
  } catch (e) {
    scanning = false;
    showMsg("err", `카메라 시작 실패: ${e}`);
  }
}

async function qrMoveStop() {
  if (!html5Qr) return;
  if (!scanning) return;
  try {
    await html5Qr.stop();
  } catch (e) {
    // ignore
  } finally {
    scanning = false;
  }
}

async function qrMoveSwitchCamera() {
  if (!cameraIds.length) {
    showMsg("err", "카메라가 없습니다.");
    return;
  }

  // 현재 인덱스 찾고 다음으로
  const idx = cameraIds.indexOf(currentCameraId);
  const next = cameraIds[(idx + 1) % cameraIds.length];
  currentCameraId = next;

  // 스캔 중이면 재시작
  const wasScanning = scanning;
  if (wasScanning) await qrMoveStop();
  showMsg("ok", "카메라 전환 완료");
  if (wasScanning) await qrMoveStart();
}

// 스캔 콜백
let lastScanAt = 0;
async function onScan(decodedText) {
  // 연속 중복 스캔 방지(0.8초)
  const now = Date.now();
  if (now - lastScanAt < 800) return;
  lastScanAt = now;

  const parsed = parseQr(decodedText);
  await applyParsed(parsed);
}

// 수동 입력 적용
async function qrMoveManual() {
  const raw = document.getElementById("manualInput").value;
  if (!raw) return;
  const parsed = parseQr(raw);
  await applyParsed(parsed);
  document.getElementById("manualInput").value = "";
}

// 초기화
function qrMoveReset() {
  state.from = "";
  state.item_code = "";
  state.lot = "";
  state.to = "";
  document.getElementById("qty").value = 1;
  refreshUI();
  showMsg("ok", "초기화 완료");
}
