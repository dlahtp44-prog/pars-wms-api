async function loadInventory() {
  const res = await fetch("/api/inventory");
  const data = await res.json();

  const tbody = document.querySelector("#inventory-table tbody");
  tbody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.item_code}</td>
      <td>${row.item_name || ""}</td>
      <td>${row.brand || ""}</td>
      <td>${row.spec || ""}</td>
      <td>${row.location_code}</td>
      <td>${row.lot}</td>
      <td style="text-align:right;">${row.quantity}</td>
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
  const d = await res.json();
  document.getElementById("dashboard").innerHTML =
    `Total Inventory: ${d.total_inventory}`;
}
