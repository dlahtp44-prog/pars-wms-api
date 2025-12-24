let qrScanner = null;

function parseQR(text){
  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k] = v;
  return o;
}

function setMsg(t){ document.getElementById("msg").innerText = t; }

function setMoveState(s){
  localStorage.setItem("move_state", JSON.stringify(s));
}
function getMoveState(){
  try { return JSON.parse(localStorage.getItem("move_state") || "{}"); }
  catch(e){ return {}; }
}
function resetMove(){
  localStorage.removeItem("move_state");
  document.getElementById("moveBox").style.display = "none";
  document.getElementById("locItems").innerHTML = "";
  setMsg("이동 플로우 초기화됨");
}

// 로케이션 재고 조회
async function loadLocationItems(warehouse, location){
  const res = await fetch(`/api/qr/location-items?warehouse=${encodeURIComponent(warehouse)}&location=${encodeURIComponent(location)}`);
  const rows = await res.json();

  const box = document.getElementById("locItems");
  if(!rows || rows.length===0){
    box.innerHTML = `<div class="muted">재고 없음</div>`;
    return;
  }
  let html = `<div class="tablewrap"><table class="table">
    <thead><tr>
      <th>품번</th><th>LOT</th><th>품명</th><th class="right">수량</th><th>선택</th>
    </tr></thead><tbody>`;
  for(const r of rows){
    html += `<tr>
      <td>${r.item_code}</td>
      <td>${r.lot_no}</td>
      <td>${(r.item_name||"")}</td>
      <td class="right">${r.qty}</td>
      <td><button class="btn" onclick="pickItem('${r.item_code}','${r.lot_no}', '${(r.item_name||"").replaceAll("'","")}','${(r.spec||"").replaceAll("'","")}')">선택</button></td>
    </tr>`;
  }
  html += `</tbody></table></div>`;
  box.innerHTML = html;
}

function pickItem(item_code, lot_no, item_name, spec){
  const s = getMoveState();
  if(!s.from_location){
    alert("먼저 출발 로케이션 QR을 스캔하세요");
    return;
  }
  s.item_code = item_code;
  s.lot_no = lot_no;
  s.item_name = item_name || "";
  s.spec = spec || "";
  setMoveState(s);
  document.getElementById("picked").innerText = `선택됨: ${item_code} / ${lot_no}`;
  document.getElementById("qty").value = 1;
  setMsg("이제 목적지 로케이션 QR을 스캔하세요");
}

// QR 처리(스캔/수동)
async function processQRText(text){
  const data = parseQR(text);
  const type = (data.type || "").toUpperCase();

  // 1) 로케이션 먼저 스캔 (MOVE 플로우)
  if(type === "LOCATION"){
    const warehouse = data.warehouse || "MAIN";
    const location = data.location || "";
    if(!location){
      setMsg("❌ location 값 없음");
      return;
    }
    const s = getMoveState();
    // 출발 로케이션이 없으면 출발로 설정, 있으면 목적지로 사용
    if(!s.from_location){
      setMoveState({ action:"MOVE", warehouse, from_location: location });
      document.getElementById("moveBox").style.display = "block";
      document.getElementById("fromLoc").innerText = location;
      setMsg("출발 로케이션 설정됨. 아래에서 이동할 제품을 선택하세요.");
      await loadLocationItems(warehouse, location);
      return;
    } else if(!s.to_location && s.from_location && s.item_code){
      s.to_location = location;
      setMoveState(s);
      document.getElementById("toLoc").innerText = location;

      // 이동 실행
      const qty = Number(document.getElementById("qty").value || 0);
      if(qty <= 0){ setMsg("❌ 수량 오류"); return; }

      const body = {
        action: "MOVE",
        warehouse: s.warehouse || "MAIN",
        from_location: s.from_location,
        to_location: s.to_location,
        item_code: s.item_code,
        item_name: s.item_name || "",
        lot_no: s.lot_no,
        spec: s.spec || "",
        qty
      };
      const res = await fetch("/api/qr/process", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify(body)
      });
      const d = await res.json();
      if(res.ok && d.ok){
        setMsg("✅ 이동 완료");
        resetMove();
      }else{
        setMsg("❌ " + (d.detail || JSON.stringify(d)));
      }
      return;
    } else {
      setMsg("이미 출발 로케이션이 설정됨. (제품 선택 후 목적지 스캔)");
      return;
    }
  }

  // 2) 제품 QR은 검색/선택 용도로만 사용(현재는 PRODUCT QR로 이동상태에 자동선택)
  if(type === "PRODUCT"){
    const s = getMoveState();
    if(s.from_location){
      pickItem(data.item_code||"", data.lot_no||"", data.item_name||"", data.spec||"");
      return;
    }
    // 이동 상태가 아니면 그냥 검색 결과 표시
    const q = (data.item_code || "") + " " + (data.lot_no || "");
    document.getElementById("manual_qr").value = `q=${q}`;
    return;
  }

  // 3) 기본 처리 (IN/OUT은 기존 방식 유지 가능)
  const action = document.getElementById("action").value;
  const body = {
    action,
    warehouse: data.warehouse || "MAIN",
    location: data.location || "",
    item_code: data.item_code || "",
    item_name: data.item_name || "",
    lot_no: data.lot_no || "",
    spec: data.spec || "",
    brand: data.brand || "",
    qty: Number(data.qty || 0)
  };

  const res = await fetch("/api/qr/process", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  const d = await res.json();
  setMsg(res.ok && d.ok ? "✅ 처리 완료" : "❌ " + (d.detail || JSON.stringify(d)));
}

// 카메라 시작(후면)
async function startScan(){
  if(qrScanner) return;
  setMsg("📷 카메라 준비 중…");

  qrScanner = new Html5Qrcode("reader");
  try{
    const cams = await Html5Qrcode.getCameras();
    if(!cams || cams.length === 0) throw "카메라 없음";

    // 후면 우선 (label이 없으면 그냥 첫번째)
    const back = cams.find(c => (c.label||"").toLowerCase().includes("back")) || cams[0];

    await qrScanner.start(
      back.id,
      { fps: 10, qrbox: 250 },
      (text)=>{
        stopScan();
        processQRText(text);
      },
      ()=>{}
    );
    setMsg("📷 스캔 중…");
  }catch(e){
    setMsg("❌ 카메라 접근 실패(권한/브라우저/https 확인)");
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
  if(!v){ alert("QR 내용을 입력하세요"); return; }
  processQRText(v);
}
