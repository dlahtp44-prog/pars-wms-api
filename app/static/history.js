async function loadHist(){
  const res = await fetch("/api/history");
  const rows = await res.json();
  const body = document.getElementById("histBody");
  let html = "";
  for(const r of rows){
    html += `
      <tr>
        <td>${r.id}</td>
        <td>${r.created_at ?? ""}</td>
        <td>${r.tx_type ?? ""}</td>
        <td>${r.warehouse ?? ""}</td>
        <td>${r.location ?? ""}</td>
        <td>${r.item_code ?? ""}</td>
        <td>${r.lot_no ?? ""}</td>
        <td class="right">${r.qty ?? ""}</td>
        <td>${r.remark ?? ""}</td>
        <td>
          <button class="btn danger" onclick="rollback(${r.id})">롤백</button>
        </td>
      </tr>
    `;
  }
  body.innerHTML = html;
}

async function rollback(id){
  if(!confirm(`이력 #${id} 를 롤백할까요?`)) return;
  const res = await fetch(`/api/history/rollback?history_id=${id}`, {method:"POST"});
  const data = await res.json();
  if(!res.ok){
    alert(data.detail ?? "롤백 실패");
    return;
  }
  alert(data.msg ?? "롤백 완료");
  loadHist();
}

loadHist();
