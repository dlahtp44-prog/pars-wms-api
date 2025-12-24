let qrScanner = null;

function parseQR(text){
  // 1) URL 전체가 들어오는 경우 ? 뒤만 파싱
  try{
    if(text.includes("?")) text = text.split("?")[1];
  }catch(e){}

  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k] = v;
  return o;
}

async function processQR(text){
  const action = document.getElementById("action").value;
  const data = parseQR(text);

  // 로케이션 QR: location만 있으면 바로 해당 로케이션 페이지로
  if(action === "LOC" || (data.location && !data.item_code)){
    const wh = data.warehouse || "MAIN";
    const loc = data.location;
    location.href = `/location?warehouse=${encodeURIComponent(wh)}&location=${encodeURIComponent(loc)}`;
    return;
  }

  // 제품 QR + 작업
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

  let d = {};
  try{ d = await res.json(); }catch(e){}

  document.getElementById("msg").innerText =
    res.ok ? "✅ 처리 완료 → 재고/이력에 반영됨" : "❌ " + (d.detail || JSON.stringify(d));
}

async function startScan(){
  if(qrScanner) return;
  document.getElementById("msg").innerText = "📷 카메라 준비 중…";

  qrScanner = new Html5Qrcode("reader");

  try{
    // 후면 카메라 우선 선택
    const cameras = await Html5Qrcode.getCameras();
    if(!cameras || cameras.length === 0) throw new Error("카메라 없음");

    let backCam = cameras.find(c => (c.label || "").toLowerCase().includes("back"));
    if(!backCam) backCam = cameras[cameras.length - 1]; // 보통 마지막이 후면인 경우 많음

    await qrScanner.start(
      { deviceId: { exact: backCam.id } },
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        stopScan();
        processQR(decodedText);
      },
      () => {}
    );

    document.getElementById("msg").innerText = "📷 스캔 중… (후면 우선)";
  }catch(e){
    // deviceId exact 실패 시 facingMode fallback
    try{
      await qrScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        (decodedText) => {
          stopScan();
          processQR(decodedText);
        },
        () => {}
      );
      document.getElementById("msg").innerText = "📷 스캔 중… (environment)";
    }catch(e2){
      document.getElementById("msg").innerText = "❌ 카메라 접근 실패: 권한/HTTPS/브라우저 확인";
      qrScanner = null;
    }
  }
}

function stopScan(){
  if(!qrScanner) return;
  qrScanner.stop().then(()=>{
    qrScanner.clear();
    qrScanner = null;
  }).catch(()=>{ qrScanner = null; });
}

function manualSearch(){
  const v = document.getElementById("manual_qr").value.trim();
  if(!v){
    alert("QR 내용을 입력하세요");
    return;
  }
  processQR(v);
}
