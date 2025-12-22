async function scan(){
  const q = document.getElementById("qr").value.trim();
  if(!q) return;

  const res = await fetch(`/api/qr-search?q=${encodeURIComponent(q)}`);
  const rows = await res.json();

  let html = "";

  if(rows.length === 0){
    html = "<p>조회 결과가 없습니다.</p>";
  } else {
    html += `
    <table border="1" style="width:100%; border-collapse:collapse;">
      <tr style="background:#ffeb3b;">
        <th>장소</th>
        <th>품번</th>
        <th>LOT</th>
        <th>로케이션</th>
        <th>수량</th>
        <th>작업</th>
      </tr>
    `;

    for(const r of rows){
      html += `
      <tr>
        <td>${r.location_name}</td>
        <td>${r.item_code}</td>
        <td>${r.lot_no}</td>
        <td>${r.location}</td>
        <td style="font-weight:bold;">${r.qty}</td>
        <td>
          <button onclick="goOutbound('${r.item_code}','${r.lot_no}','${r.location}')">출고</button>
          <button onclick="goMove('${r.item_code}','${r.lot_no}','${r.location}')">이동</button>
        </td>
      </tr>
      `;
    }
    html += "</table>";
  }

  document.getElementById("result").innerHTML = html;
}

function goOutbound(item, lot, loc){
  location.href =
    `/outbound-page?item_code=${item}&lot_no=${lot}&location=${loc}`;
}

function goMove(item, lot, loc){
  location.href =
    `/move-page?item_code=${item}&lot_no=${lot}&from_location=${loc}`;
}
navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
.then(stream => {
  document.getElementById("video").srcObject = stream;
});
