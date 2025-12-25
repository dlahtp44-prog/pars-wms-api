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
  const table = document.getElementById("history");
  table.innerHTML = "<tr><th>Action</th><th>Item</th><th>Qty</th><th>Date</th></tr>";
  data.forEach(r => {
    table.innerHTML += `<tr>
      <td>${r.action}</td>
      <td>${r.item_code}</td>
      <td>${r.quantity}</td>
      <td>${r.created_at}</td>
    </tr>`;
  });
}

async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  const d = await res.json();
  document.getElementById("dashboard").innerHTML =
    `Total Inventory: ${d.total_inventory}`;
}
