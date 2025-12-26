async function loadHistory() {
  const res = await fetch("/api/history");
  const data = await res.json();

  const tbody = document.querySelector("#history-table tbody");
  tbody.innerHTML = "";

  // ------------------------------
  // 구분 한글 매핑
  // ------------------------------
  const actionMap = {
    "INBOUND": "입고",
    "OUTBOUND": "출고",
    "MOVE": "이동"
  };

  data.forEach(row => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${actionMap[row.action] || row.action}</td>
      <td>${row.item_code}</td>
      <td>${row.location_from || ""}</td>
      <td>${row.location_to || ""}</td>
      <td>${row.lot}</td>
      <td style="text-align:right;">${row.quantity}</td>
      <td>${row.created_at.replace("T", " ")}</td>
    `;

    tbody.appendChild(tr);
  });
}



async function loadHistory() {
  const res = await fetch("/api/history");
  const data = await res.json();

  const tbody = document.querySelector("#history-table tbody");
  tbody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.action}</td>
      <td>${row.item_code}</td>
      <td>${row.location_from || ""}</td>
      <td>${row.location_to || ""}</td>
      <td>${row.lot}</td>
      <td style="text-align:right;">${row.quantity}</td>
      <td>${row.created_at.replace("T", " ")}</td>
    `;
    tbody.appendChild(tr);
  });
}


async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  const data = await res.json();

  document.getElementById("totalInventory").innerText =
    data.total_inventory;
}

