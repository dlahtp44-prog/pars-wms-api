let stream = null;
let rafId = null;

const video = () => document.getElementById("preview");
const canvas = () => document.getElementById("canvas");
const resultBox = () => document.getElementById("result");

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false
    });
    video().srcObject = stream;
    await video().play();
    scanLoop();
  } catch (e) {
    alert("카메라 권한 또는 HTTPS 확인 필요: " + e);
  }
}

function stopCamera() {
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
}

function scanLoop() {
  const v = video();
  const c = canvas();
  const ctx = c.getContext("2d");

  if (v.readyState === v.HAVE_ENOUGH_DATA) {
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    ctx.drawImage(v, 0, 0, c.width, c.height);

    const img = ctx.getImageData(0, 0, c.width, c.height);
    const code = jsQR(img.data, img.width, img.height);

    if (code && code.data) {
      // 한번 읽히면 중지하고 조회
      stopCamera();
      document.getElementById("qrText").value = code.data;
      manualSearch();
      return;
    }
  }

  rafId = requestAnimationFrame(scanLoop);
}

async function manualSearch() {
  const q = document.getElementById("qrText").value.trim();
  if (!q) return;

  const res = await fetch(`/api/qr-search?q=${encodeURIComponent(q)}`);
  const rows = await res.json();

  if (!rows.length) {
    resultBox().innerHTML = "<p>조회 결과 없음</p>";
    return;
  }

  let html = `
  <div class="tablewrap">
    <table class="table">
      <thead>
        <tr>
          <th>창고</th><th>로케이션</th><th>브랜드</th><th>품번</th><th>품명</th><th>LOT</th><th>규격</th>
          <th class="right">수량</th>
          <th>바로 작업</th>
        </tr>
      </thead><tbody>
  `;

  for (const r of rows) {
    html += `
      <tr>
        <td>${r.warehouse||""}</td>
        <td>${r.location||""}</td>
        <td>${r.brand||""}</td>
        <td>${r.item_code||""}</td>
        <td>${r.item_name||""}</td>
        <td>${r.lot_no||""}</td>
        <td>${r.spec||""}</td>
        <td class="right"><b>${r.qty||0}</b></td>
        <td>
          <a class="smallbtn" href="/outbound-page?warehouse=${encodeURIComponent(r.warehouse||"")}&location=${encodeURIComponent(r.location||"")}&item_code=${encodeURIComponent(r.item_code||"")}&lot_no=${encodeURIComponent(r.lot_no||"")}">출고</a>
          <a class="smallbtn gray" href="/move-page?warehouse=${encodeURIComponent(r.warehouse||"")}&from_location=${encodeURIComponent(r.location||"")}&item_code=${encodeURIComponent(r.item_code||"")}&lot_no=${encodeURIComponent(r.lot_no||"")}">이동</a>
        </td>
      </tr>
    `;
  }

  html += "</tbody></table></div>";
  resultBox().innerHTML = html;
}
