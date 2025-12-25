// QR 생성: 서버 설치 없이 CDN으로 처리
// 라벨 출력은 오프라인/내부망 환경도 고려해두면 나중에 파일로 내장할 수 있음.

function makeQR(canvasId, text){
  // 동적으로 qrious 로드
  loadQrious().then(()=>{
    const canvas = document.getElementById(canvasId);
    // eslint-disable-next-line no-undef
    new QRious({
      element: canvas,
      value: text,
      size: 220
    });
  });
}

function loadQrious(){
  return new Promise((resolve, reject)=>{
    if(window.QRious) return resolve();
    const s = document.createElement("script");
    s.src = "https://unpkg.com/qrious@4.0.2/dist/qrious.min.js";
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

function escapeHtml(s){
  return (s||"").replace(/[&<>"']/g, (m)=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m]));
}
