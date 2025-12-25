// app/static/qr_camera.js
let qrScanner = null;

function parseQR(text){
  // "type=LOC&location=D01-01" 같은 querystring 형태를 파싱
  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k] = v;
  return o;
}

async function processQR(text){
  const action = document.getElementById("action").value;
  const msg = document.getElementById("msg");

  try{
    const data = parseQR(text);

    const body = {
      action,
      warehouse: data.warehouse || "MAIN",
      location: data.location || "",
      from_location: data.from_location || "",
      to_location: data.to_location || "",
      brand: data.brand || "",
      item_code: data.item_code || "",
      item_name: data.item_name || "",
      lot_no: data.lot_no || "",
      spec: data.spec || "",
      qty: Number(data.qty || 0)
    };

    const res = await fetch("/api/qr/process", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });
    const d = await res.json();

    msg.innerText = res.ok && d.ok
      ? "✅ 처리 완료: " + JSON.stringify(d)
      : "❌ " + (d.detail || JSON.stringify(d));
  }catch(e){
    msg.innerText = "❌ QR 파싱 실패: " + e;
  }
}

async function startScan(){
  const msg = document.getElementById("msg");
  if(qrScanner) return;

  msg.innerText = "📷 카메라 준비 중…";

  qrScanner = new Html5Qrcode("reader");

  try{
    const cameras = await Html5Qrcode.getCameras();
    if(!cameras || cameras.length === 0) throw "카메라 없음";

    // 후면(back/environment) 우선
    const backCam =
      cameras.find(c => (c.label||"").toLowerCase().includes("back")) ||
      cameras.find(c => (c.label||"").toLowerCase().includes("rear")) ||
      cameras[0];

    await qrScanner.start(
      backCam.id,
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        stopScan();
        processQR(decodedText);
      },
      () => {}
    );

    msg.innerText = "📷 스캔 중…";
  }catch(e){
    msg.innerText = "❌ 카메라 접근 실패(권한/https/브라우저): " + e;
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

function manualSend(){
  const v = document.getElementById("manual_qr").value.trim();
  if(!v) return alert("QR 내용을 입력하세요");
  processQR(v);
}
