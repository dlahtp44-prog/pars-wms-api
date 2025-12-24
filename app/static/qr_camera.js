let qrScanner = null;

/* QR 파싱 */
function parseQR(text){
  // URL이든 querystring이든 모두 처리
  if(text.startsWith("http")){
    const u = new URL(text);
    if(u.pathname.startsWith("/loc/")){
      return { type:"LOC", location: u.pathname.split("/").pop() };
    }
    const p = {};
    u.searchParams.forEach((v,k)=>p[k]=v);
    return p;
  }

  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k]=v;
  return o;
}

/* QR 스캔 처리 */
async function processQR(text){
  const data = parseQR(text);
  const msg = document.getElementById("msg");

  /* 1️⃣ 로케이션 QR */
  if(data.type === "LOC" || data.location){
    const loc = data.location;

    // 아직 이동 시작 전 → 출발 로케이션
    if(!sessionStorage.getItem("move_from")){
      sessionStorage.setItem("move_from", loc);
      msg.innerText = `📍 출발 위치 설정: ${loc}\n이동할 제품을 선택하세요`;
      window.location.href = `/loc/${loc}`;
      return;
    }

    // 이동 대상 제품이 선택된 상태 → 도착 로케이션
    const moveItem = JSON.parse(sessionStorage.getItem("move_item") || "null");
    if(moveItem){
      await doMove(loc);
      return;
    }

    msg.innerText = "❌ 이동할 제품이 선택되지 않았습니다";
    return;
  }

  msg.innerText = "❌ 인식 불가 QR";
}

/* 실제 이동 처리 */
async function doMove(toLocation){
  const from = sessionStorage.getItem("move_from");
  const item = JSON.parse(sessionStorage.getItem("move_item"));
  const msg = document.getElementById("msg");

  const body = {
    warehouse: "MAIN",
    from_location: from,
    to_location: toLocation,
    item_code: item.item_code,
    lot_no: item.lot_no,
    qty: item.qty
  };

  const res = await fetch("/api/move", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });

  const d = await res.json();

  if(res.ok){
    msg.innerText = `✅ 이동 완료\n${from} → ${toLocation}`;
    sessionStorage.clear();
  }else{
    msg.innerText = "❌ 이동 실패: " + (d.detail || "");
  }
}

/* 카메라 시작 (후면 우선 – 이미 확인됨) */
async function startScan(){
  if(qrScanner) return;
  qrScanner = new Html5Qrcode("reader");

  try{
    const cams = await Html5Qrcode.getCameras();
    const back =
      cams.find(c => c.label.toLowerCase().includes("back")) ||
      cams[cams.length - 1];

    await qrScanner.start(
      { deviceId: { exact: back.id } },
      { fps: 10, qrbox: 250 },
      (text)=>{ stopScan(); processQR(text); },
      ()=>{}
    );
  }catch(e){
    await qrScanner.start(
      { facingMode:"environment" },
      { fps:10, qrbox:250 },
      (text)=>{ stopScan(); processQR(text); },
      ()=>{}
    );
  }
}

function stopScan(){
  if(!qrScanner) return;
  qrScanner.stop().then(()=>{
    qrScanner.clear();
    qrScanner = null;
  });
}
