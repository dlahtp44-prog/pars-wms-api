// app/static/qr_camera.js
let qrScanner = null;
let state = {
  mode: "LOC_FIRST",       // LOC_FIRST -> PICK_ITEM -> LOC_TO
  fromLoc: "",
  item_code: "",
  lot_no: "",
  qty: 0
};

function setMsg(t){ document.getElementById("msg").innerText = t; }

function isUrlLike(text){
  return text.startsWith("http://") || text.startsWith("https://") || text.startsWith("/loc/");
}
function parseQuery(text){
  const params = new URLSearchParams(text);
  const o = {};
  for(const [k,v] of params.entries()) o[k]=v;
  return o;
}

async function apiGet(url){
  const r = await fetch(url);
  const d = await r.json().catch(()=> ({}));
  if(!r.ok) throw (d.detail || JSON.stringify(d));
  return d;
}
async function apiPost(url, body){
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)});
  const d = await r.json().catch(()=> ({}));
  if(!r.ok) throw (d.detail || JSON.stringify(d));
  return d;
}

async function renderLocItems(loc){
  const rows = await apiGet(`/api/qr-search?location=${encodeURIComponent(loc)}`);
  const box = document.getElementById("result");
  if(!rows.length){
    box.innerHTML = `<div class="muted">재고 없음</div>`;
    return;
  }
  let html = `<div class="h3">📦 ${loc} 재고</div>
  <div class="tablewrap"><table class="table">
  <thead><tr><th>품번</th><th>LOT</th><th class="right">수량</th><th>선택</th></tr></thead><tbody>`;
  for(const r of rows){
    html += `<tr>
      <td>${r.item_code}</td>
      <td>${r.lot_no}</td>
      <td class="right"><b>${r.qty}</b></td>
      <td><button class="btn" onclick="pickItem('${loc}','${r.item_code}','${r.lot_no}')">이동선택</button></td>
    </tr>`;
  }
  html += `</tbody></table></div>`;
  box.innerHTML = html;
}

window.pickItem = function(loc, item_code, lot_no){
  const qty = Number(prompt("이동 수량 입력", "1") || "0");
  if(!qty || qty<=0){ alert("수량이 올바르지 않습니다."); return; }
  state.mode = "LOC_TO";
  state.fromLoc = loc;
  state.item_code = item_code;
  state.lot_no = lot_no;
  state.qty = qty;
  setMsg(`✅ 선택됨: ${item_code}/${lot_no} 수량 ${qty}. 이제 '목적 로케이션 QR'을 스캔하세요.`);
};

async function handleScan(text){
  // URL 라벨이면: /loc/XXX 형태를 loc로 사용
  if(isUrlLike(text)){
    if(text.startsWith("/loc/")){
      const loc = text.replace("/loc/","").trim();
      if(!loc) return;
      if(state.mode === "LOC_FIRST"){
        state.fromLoc = loc;
        state.mode = "PICK_ITEM";
        setMsg(`✅ 출발 로케이션: ${loc}. 아래 목록에서 이동할 제품을 선택하세요.`);
        await renderLocItems(loc);
        return;
      }
      if(state.mode === "LOC_TO"){
        const toLoc = loc;
        // 이동 실행
        await apiPost("/api/move", {
          warehouse: "MAIN",
          from_location: state.fromLoc,
          to_location: toLoc,
          item_code: state.item_code,
          lot_no: state.lot_no,
          qty: state.qty
        });
        setMsg(`✅ 이동 완료: ${state.fromLoc} -> ${toLoc}`);
        state = {mode:"LOC_FIRST", fromLoc:"", item_code:"", lot_no:"", qty:0};
        document.getElementById("result").innerHTML = "";
        return;
      }
      return;
    }
    // 절대 URL이면 그냥 열어도 됨(선택)
    // location.href = text;
    return;
  }

  // 제품 QR(쿼리스트링)로 들어오는 경우
  const data = parseQuery(text);

  // 로케이션 QR을 text로 만들었으면 location=... 이 있을 수도 있음
  const loc = (data.location || "").trim();
  if(loc){
    if(state.mode === "LOC_FIRST"){
      state.fromLoc = loc;
      state.mode = "PICK_ITEM";
      setMsg(`✅ 출발 로케이션: ${loc}. 아래 목록에서 이동할 제품을 선택하세요.`);
      await renderLocItems(loc);
      return;
    }
    if(state.mode === "LOC_TO"){
      const toLoc = loc;
      await apiPost("/api/move", {
        warehouse: data.warehouse || "MAIN",
        from_location: state.fromLoc,
        to_location: toLoc,
        item_code: state.item_code,
        lot_no: state.lot_no,
        qty: state.qty
      });
      setMsg(`✅ 이동 완료: ${state.fromLoc} -> ${toLoc}`);
      state = {mode:"LOC_FIRST", fromLoc:"", item_code:"", lot_no:"", qty:0};
      document.getElementById("result").innerHTML = "";
      return;
    }
    return;
  }

  // 제품 QR을 스캔하면: (IN/OUT는 기존 /api/qr/process로)
  // 이동은 지금 “로케이션 먼저” 정책이므로 여기서는 안내만
  if(data.item_code && data.lot_no){
    setMsg("ℹ️ 제품 QR 인식됨. '로케이션 먼저 스캔' 방식에서는 로케이션을 먼저 스캔해 주세요.");
  }
}

async function startScan(){
  if(qrScanner) return;
  setMsg("📷 카메라 준비 중…");

  const Html5Qrcode = window.Html5Qrcode;
  qrScanner = new Html5Qrcode("reader");

  try{
    const cameras = await Html5Qrcode.getCameras();
    if(!cameras || cameras.length === 0) throw "카메라 없음";

    // 후면 카메라 우선
    const back = cameras.find(c => (c.label||"").toLowerCase().includes("back")) || cameras[cameras.length-1];

    await qrScanner.start(
      back.id,
      { fps: 10, qrbox: 250 },
      async (text)=>{
        await stopScan();
        try{ await handleScan(text); }
        catch(e){ setMsg("❌ " + e); }
      },
      ()=>{}
    );
    setMsg("📷 스캔 중…");
  }catch(e){
    setMsg("❌ 카메라 접근 실패(권한/HTTPS/브라우저 확인)");
    qrScanner = null;
  }
}

async function stopScan(){
  if(!qrScanner) return;
  await qrScanner.stop();
  qrScanner.clear();
  qrScanner = null;
}

window.startScan = startScan;
window.stopScan = stopScan;
