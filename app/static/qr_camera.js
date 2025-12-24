let qrScanner = null;

async function startScan(){
  const msg = document.getElementById("msg");
  msg.innerText = "📷 카메라 준비 중…";

  if(qrScanner) return;

  try{
    qrScanner = new Html5Qrcode("reader");

    const cameras = await Html5Qrcode.getCameras();
    if(!cameras || cameras.length === 0){
      throw "카메라 없음";
    }

    const backCam =
      cameras.find(c => c.label.toLowerCase().includes("back")) || cameras[0];

    await qrScanner.start(
      backCam.id,
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        stopScan();
        processQR(decodedText);
      }
    );

    msg.innerText = "📷 스캔 중…";
  }catch(e){
    msg.innerText = "❌ 카메라 접근 실패 (권한/HTTPS 확인)";
    qrScanner = null;
  }
}

function stopScan(){
  if(!qrScanner) return;
  qrScanner.stop().then(()=>{
    qrScanner.clear();
    qrScanner = null;
  });
}

async function processQR(text){
  try{
    const params = new URLSearchParams(text);
    const data = Object.fromEntries(params.entries());

    const res = await fetch("/api/qr/process", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(data)
    });

    const d = await res.json();
    document.getElementById("msg").innerText =
      res.ok ? "✅ 처리 완료" : "❌ " + JSON.stringify(d);
  }catch(e){
    document.getElementById("msg").innerText = "❌ QR 처리 실패";
  }
}
