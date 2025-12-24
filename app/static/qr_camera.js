let qrScanner = null;

function parseQR(text){
  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k] = v;
  return o;
}

async function processQR(text){
  try{
    const data = parseQR(text);
    const action = document.getElementById("action").value;

    const body = {
      action,
      warehouse: data.warehouse || "MAIN",
      location: data.location || "",
      from_location: data.from_location || data.from || "",
      to_location: data.to_location || data.to || "",
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
    document.getElementById("msg").innerText =
      res.ok && d.ok ? "✅ 처리 완료" : "❌ " + (d.detail || JSON.stringify(d));
  }catch(e){
    document.getElementById("msg").innerText = "❌ QR 파싱 실패: " + e;
  }
}

async function startScan(){
  if(qrScanner) return;

  document.getElementById("msg").innerText = "📷 카메라 준비 중…";
  qrScanner = new Html5Qrcode("reader");

  try{
    const cams = await Html5Qrcode.getCameras();
    if(!cams || cams.length === 0) throw "카메라 없음";

    // 후면(back/environment) 라벨이 있으면 우선
    const back =
      cams.find(c => (c.label || "").toLowerCase().includes("back")) ||
      cams.find(c => (c.label || "").toLowerCase().includes("rear")) ||
      cams[0];

    await qrScanner.start(
      back.id,
      { fps: 10, qrbox: 250 },
      (text)=>{
        stopScan();
        processQR(text);
      },
      ()=>{}
    );

    document.getElementById("msg").innerText = "📷 스캔 중… (후면 우선)";
  }catch(e){
    document.getElementById("msg").innerText = "❌ 카메라 접근 실패: 권한/브라우저(HTTPS) 확인";
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

function manualSearch(){
  const v = document.getElementById("manual_qr").value.trim();
  if(!v){
    alert("QR 내용을 입력하세요");
    return;
  }
  processQR(v);
}
