// app/static/qr_camera.js
let qrScanner = null;

async function startScan() {
  if (qrScanner) return;

  document.getElementById("msg").innerText = "📷 카메라 준비 중…";

  qrScanner = new Html5Qrcode("reader");

  try {
    const cameras = await Html5Qrcode.getCameras();
    if (!cameras || cameras.length === 0) {
      throw new Error("카메라 없음");
    }

    // 👉 후면 카메라 우선 선택
    let selectedCamera =
      cameras.find(c =>
        c.label.toLowerCase().includes("back") ||
        c.label.toLowerCase().includes("rear")
      ) || cameras[cameras.length - 1];

    await qrScanner.start(
      selectedCamera.id,
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        stopScan();
        processQR(decodedText);
      }
    );

    document.getElementById("msg").innerText = "📷 스캔 중…";
  } catch (e) {
    document.getElementById("msg").innerText =
      "❌ 카메라 접근 실패 (권한 또는 HTTPS 확인)";
    qrScanner = null;
  }
}

function stopScan() {
  if (!qrScanner) return;
  qrScanner.stop().then(() => {
    qrScanner.clear();
    qrScanner = null;
  });
}


function manualSend(){
  const v = document.getElementById("manual_qr").value.trim();
  if(!v) return alert("QR 내용을 입력하세요");
  processQR(v);
}
