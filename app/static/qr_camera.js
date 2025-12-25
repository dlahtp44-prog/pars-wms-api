// app/static/qr_camera.js
let qrScanner = null;
let camerasCache = [];
let stage = "LOCATION_FROM"; // LOCATION_FROM -> PICK_ITEM -> LOCATION_TO
let selected = { warehouse: "MAIN", from_location: "", to_location: "", item_code: "", lot_no: "", qty: 0 };

function parseParams(text){
  // QR이 "warehouse=MAIN&location=D01-01" 같은 형태라고 가정
  const p = new URLSearchParams(text.trim());
  const o = {};
  for (const [k,v] of p.entries()) o[k] = v;
  return o;
}

async function ensureCameras(){
  camerasCache = await Html5Qrcode.getCameras();
  if(!camerasCache || camerasCache.length === 0) throw new Error("카메라 없음");

  const sel = document.getElementById("cameraSel");
  sel.innerHTML = "";
  camerasCache.forEach((c, i) => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.label || `camera-${i+1}`;
    sel.appendChild(opt);
  });

  // 후면 우선
  const back = camerasCache.find(c => (c.label||"").toLowerCase().includes("back") || (c.label||"").toLowerCase().includes("rear"));
  if(back) sel.value = back.id;
  else sel.value = camerasCache[camerasCache.length-1].id;
}

async function startScan(){
  if(qrScanner) return;

  setMsg("📷 카메라 준비 중…");
  qrScanner = new Html5Qrcode("reader");

  try{
    await ensureCameras();
    const camId = document.getElementById("cameraSel").value;

    await qrScanner.start(
      camId,
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        // 한 번 읽으면 멈추고 처리(오작동 방지)
        stopScan();
        onScanned(decodedText);
      }
    );

    setMsg("📷 스캔 중…");
  }catch(e){
    setMsg("❌ 카메라 접근 실패(권한/HTTPS/브라우저 확인)");
    qrScanner = null;
  }
}

function stopScan(){
  if(!qrScanner) return;
  qrScanner.stop().then(() => {
    qrScanner.clear();
    qrScanner = null;
  });
}

function setMsg(t){
  const el = document.getElementById("msg");
  if(el) el.innerText = t;
}

async function onScanned(text){
  try{
    const data = parseParams(text);

    if(stage === "LOCATION_FROM"){
      // 로케이션 QR
      const wh = data.warehouse || "MAIN";
      const loc = data.location || data.from_location || "";
      if(!loc) return setMsg("❌ 로케이션 QR이 아닙니다 (location= 필요)");

      selected.warehouse = wh;
      selected.from_location = loc;

      // 해당 위치 재고 불러오기
      const res = await fetch(`/api/location-items?warehouse=${encodeURIComponent(wh)}&location=${encodeURIComponent(loc)}`);
      const rows = await res.json();
      renderPickList(rows);

      stage = "PICK_ITEM";
      setStage();
      setMsg(`✅ 출발 로케이션: ${loc} / 이동할 품목을 선택하세요`);
      return;
    }

    if(stage === "LOCATION_TO"){
      const loc2 = data.location || data.to_location || "";
      if(!loc2) return setMsg("❌ 목적지 로케이션 QR이 아닙니다 (location= 필요)");
      selected.to_location = loc2;

      // 이동 실행
      const body = {
        warehouse: selected.warehouse,
        item_code: selected.item_code,
        lot_no: selected.lot_no,
        qty: Number(selected.qty),
        from_location: selected.from_location,
        to_location: selected.to_location,
      };

      const res = await fetch("/api/move/manual", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(body)
      });

      const d = await res.json();
      if(!res.ok) return setMsg("❌ 이동 실패: " + (d.detail || JSON.stringify(d)));

      // 초기화
      stage = "LOCATION_FROM";
      selected = { warehouse: "MAIN", from_location: "", to_location: "", item_code: "", lot_no: "", qty: 0 };
      renderPickList([]);
      setStage();
      setMsg("✅ 이동 완료! 다음 출발 로케이션 QR을 스캔하세요");
      return;
    }

  }catch(e){
    setMsg("❌ QR 처리 실패");
  }
}

function renderPickList(rows){
  const box = document.getElementById("pickList");
  if(!box) return;

  if(!rows || rows.length === 0){
    box.innerHTML = "<div class='muted'>재고가 없습니다.</div>";
    return;
  }

  let html = `<table class="table">
    <thead><tr>
      <th>품번</th><th>LOT</th><th class="right">수량</th><th></th>
    </tr></thead><tbody>`;

  for(const r of rows){
    html += `<tr>
      <td>${r.item_code}</td>
      <td>${r.lot_no}</td>
      <td class="right"><b>${r.qty}</b></td>
      <td><button class="btn" onclick="pickItem('${r.item_code}','${r.lot_no}',${r.qty})">선택</button></td>
    </tr>`;
  }

  html += "</tbody></table>";
  box.innerHTML = html;
}

function pickItem(item_code, lot_no, maxQty){
  const qty = Number(prompt(`이동 수량 입력 (최대 ${maxQty})`, String(maxQty)));
  if(!qty || qty <= 0) return;

  selected.item_code = item_code;
  selected.lot_no = lot_no;
  selected.qty = qty;

  stage = "LOCATION_TO";
  setStage();
  setMsg(`✅ 선택됨: ${item_code} / ${lot_no} / ${qty}개 → 목적지 로케이션 QR을 스캔하세요`);
}

function setStage(){
  const el = document.getElementById("stage");
  if(!el) return;
  if(stage === "LOCATION_FROM") el.innerText = "1) 출발 로케이션 QR 스캔";
  if(stage === "PICK_ITEM") el.innerText = "2) 이동할 품목 선택";
  if(stage === "LOCATION_TO") el.innerText = "3) 목적지 로케이션 QR 스캔";
}
