let stream = null;
let detector = null;
let scanning = false;

function parseQR(text){
  // "ITEM=...;WH=...;LOC=...;LOT=...;QTY=..." 형태 지원
  const out = { raw: text };
  try {
    // JSON 형태면 JSON
    if(text.trim().startsWith("{")){
      const j = JSON.parse(text);
      return { ...out, ...j };
    }
  } catch(e) {}

  const parts = text.split(";").map(s=>s.trim()).filter(Boolean);
  for(const p of parts){
    const [k,v] = p.split("=").map(s=>s.trim());
    if(!k || v===undefined) continue;
    out[k.toLowerCase()] = v;
  }
  return out;
}

async function startScan(){
  const hint = document.getElementById("scanHint");
  const video = document.getElementById("preview");

  if(!("BarcodeDetector" in window)){
    hint.textContent = "❌ 이 브라우저는 실시간 QR 스캔을 지원하지 않습니다. (수동 입력 사용)";
    return;
  }

  detector = new BarcodeDetector({formats:["qr_code"]});
  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "environment" },
    audio: false
  });

  video.srcObject = stream;
  await video.play();
  scanning = true;
  hint.textContent = "✅ 스캔 중... QR을 카메라에 비추세요";

  scanLoop();
}

async function scanLoop(){
  if(!scanning) return;
  const video = document.getElementById("preview");

  try{
    const barcodes = await detector.detect(video);
    if(barcodes && barcodes.length > 0){
      const text = barcodes[0].rawValue || "";
      document.getElementById("qrText").value = text;
      await lookup();     // 스캔되면 바로 조회
      stopScan();         // 한번 읽으면 자동 정지
      return;
    }
  }catch(e){}

  requestAnimationFrame(scanLoop);
}

function stopScan(){
  scanning = false;
  const hint = document.getElementById("scanHint");
  hint.textContent = "정지됨";
  const video = document.getElementById("preview");
  video.pause();
  if(stream){
    for(const t of stream.getTracks()) t.stop();
  }
  stream = null;
}

async function lookup(){
  const text = document.getElementById("qrText").value.trim();
  if(!text){
    alert("QR 값(또는 품번/LOT)을 입력하세요.");
    return;
  }

  const q = parseQR(text);
  // 조회 키워드 우선순위: item > ITEM > item_code > raw
  const keyword =
    q.item_code || q.item || q.itemcode || q["item"] || q["item_code"] ||
    q["item"] || q["item_code"] || q.raw;

  const res = await fetch(`/api/inventory/search?q=${encodeURIComponent(keyword)}`);
  const data = await res.json();

  const body = document.getElementById("invBody");
  let html = "";
  for(const r of data.rows){
    html += `
      <tr>
        <td>${r.warehouse ?? ""}</td>
        <td>${r.location ?? ""}</td>
        <td>${r.brand ?? ""}</td>
        <td>${r.item_code ?? ""}</td>
        <td>${r.item_name ?? ""}</td>
        <td>${r.lot_no ?? ""}</td>
        <td>${r.spec ?? ""}</td>
        <td class="right">${r.qty ?? ""}</td>
      </tr>
    `;
  }
  body.innerHTML = html || `<tr><td colspan="8">조회 결과 없음</td></tr>`;
}
