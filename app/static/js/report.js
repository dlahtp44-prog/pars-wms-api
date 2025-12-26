const actionMap = {
  "INBOUND": "입고",
  "OUTBOUND": "출고",
  "MOVE": "이동"
};

async function loadReport() {
  const action = document.getElementById("action").value;
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  const params = new URLSearchParams();
  if (action) params.append("action", action);
  if (start) params.append("start_date", start);
  if (end) params.append("end_date", end);

  const res = await fetch("/api/report?" + params.toString());
  const data = await res.json();

  const tbody = document.getElementById("reportBody");
  tbody.innerHTML = "";

  data.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${actionMap[r.action] || r.action}</td>
      <td>${r.item_code}</td>
      <td>${r.lot || ""}</td>
      <td>${r.location_from || ""}</td>
      <td>${r.location_to || ""}</td>
      <td style="text-align:right">${r.quantity}</td>
      <td>${r.created_at.replace("T", " ")}</td>
    `;
    tbody.appendChild(tr);
  });
}
