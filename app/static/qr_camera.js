// app/static/qr_camera.js
let qrScanner = null;
let currentCameraId = null;
let camerasCache = [];

/* 카메라 목록 로드 */
async function loadCameras() {
  if (camerasCache.length > 0) return camerasCache;
  camerasCache = await Html5Qrcode.getCameras();
  return camerasCache;
}

/* 카메라 시작 */
async function startScan(prefer = "back") {
  if (qrScanner) return;

  document.getElementById("msg").innerText = "📷 카메라 준비 중…";
  qrScanner = new Html5Qrcode("reader");

  try {
    const cameras = await loadCameras();
    if (!cameras || cameras.length === 0) throw new Error("카메라 없음");

    // 🔹 후면/전면 선택 로직
    let cam =
      prefer === "front"
        ? cameras.find(c => c.label.toLowerCase().includes("front"))
        : cameras.find(c =>
            c.label.toLowerCase().includes("back") ||
            c.label.toLowerCase().includes("rear")
          );

    if (!cam) cam = cameras[cameras.length - 1]; // fallback

    currentCameraId = cam.id;

    await qrScanner.start(
      cam.id,
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        stopScan();
        processQR(decodedText);
      }
    );

    document.getElementById("msg").innerText =
      `📷 스캔 중 (${cam.label || "Camera"})`;
  } catch (e) {
    document.getElementById("msg").innerText =
      "❌ 카메라 접근 실패 (HTTPS/권한 확인)";
    qrScanner = null;
  }
}

/* 카메라 전환 */
async function switchCamera() {
  if (!qrScanner) return;

  const cameras = await loadCameras();
  if (cameras.length < 2) {
    alert("전환 가능한 카메라가 없습니다");
    return;
  }

  const idx = cameras.findIndex(c => c.id === currentCameraId);
  const next = cameras[(idx + 1) % cameras.length];

  await qrScanner.stop();
  await qrScanner.clear();

  currentCameraId = next.id;
  await qrScanner.start(
    next.id,
    { fps: 10, qrbox: 250 },
    (text) => {
      stopScan();
      processQR(text);
    }
  );

  document.getElementById("msg").innerText =
    `📷 전환됨 (${next.label || "Camera"})`;
}

/* 중지 */
function stopScan() {
  if (!qrScanner) return;
  qrScanner.stop().then(() => {
    qrScanner.clear();
    qrScanner = null;
  });
}

/* 수동 입력 */
function manualSend() {
  const v = document.getElementById("manual_qr").value.trim();
  if (!v) return alert("QR 내용을 입력하세요");
  processQR(v);
}
