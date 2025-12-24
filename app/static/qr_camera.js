let qrScanner = null;

async function startScan(){
  if(qrScanner) return;

  const msg = document.getElementById("msg");
  msg.innerText = "📷 카메라 준비 중…";

  qrScanner = new Html5Qrcode("reader");

  try{
    const cameras = await Html5Qrcode.getCameras();
    if(!cameras.length) throw "카메라 없음";

    // 🔥 후면 카메라 우선
    const back =
      cameras.find(c => c.label.toLowerCase().includes("back")) || cameras[cameras.length-1];

    await qrScanner.start(
      back.id,
      { fps: 10, qrbox: 250 },
      text => {
        stopScan();
        processQR(text);
      }
    );

    msg.innerText = "📷 스캔 중…";
  }catch(e){
    msg.innerText = "❌ 카메라 접근 실패 (HTTPS/권한 확인)";
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
