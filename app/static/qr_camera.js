let qrScanner = null;

function parseQR(text){
  // "item_code=AAA&lot_no=1&location=A01&qty=1" 형태
  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k] = v;
  return o;
}

async function processQR(text){
  const msg = document.getElementById("msg");
  try{
    const data = parseQR(text);
    const action = document.getElementById("action").value;

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

    if(!body.item_code || !body.qty){
      msg.innerText = "❌ QR 데이터에 item_code / qty가 필요합니다.";
      return;
    }
    if(action === "MOVE" && (!body.from_location || !body.to_location)){
      msg.innerText = "❌ MOVE는 from_location, to_location이 필요합니다.";
      return;
    }
    if((action === "IN" || action === "OUT") && !body.location){
      msg.innerText = "❌ IN/OUT는 location이 필요합니다.";
      return;
    }

    const res = await fetch("/api/qr/process", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });
    const d = await res.json().catch(()=>({}));
    msg.innerText = res.ok ? "✅ 처리 완료" : ("❌ " + (d.detail || JSON.stringify(d)));
  }catch(e){
    msg.innerText = "❌ 처리 실패: " + e;
  }
}

async function startScan(){
  const msg = document.getElementById("msg");
  msg.innerText = "📷 카메라 준비 중…";

  if(!window.isSecureContext){
    msg.innerText = "❌ HTTPS에서만 카메라가 동작합니다.";
    return;
  }
  if(qrScanner) return;

  try{
    qrScanner = new Html5Qrcode("reader");
    const cameras = await Html5Qrcode.getCameras();
    if(!cameras || cameras.length === 0) throw "카메라 없음";

    const back = cameras.find(c => (c.label||"").toLowerCase().includes("back")) || cameras[0];

    await qrScanner.start(
      back.id,
      { fps: 10, qrbox: 250 },
      (text)=>{
        stopScan();
        processQR(text);
      },
      ()=>{}
    );
    msg.innerText = "📷 스캔 중…";
  }catch(e){
    msg.innerText = "❌ 카메라 접근 실패(권한/브라우저/HTTPS 확인)";
    qrScanner = null;
  }
}

function stopScan(){
  if(!qrScanner) return;
  qrScanner.stop().then(()=>{
    qrScanner.clear();
    qrScanner = null;
    const msg = document.getElementById("msg");
    if(msg) msg.innerText = "⏹ 중지됨";
  }).catch(()=>{
    qrScanner = null;
  });
}

function manualSearch(){
  const v = document.getElementById("manual_qr").value.trim();
  if(!v){ alert("QR 내용을 입력하세요"); return; }
  processQR(v);
}
