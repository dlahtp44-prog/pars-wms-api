async function loadInventory() {
  const res = await fetch("/api/inventory");
  const data = await res.json();
  const table = document.getElementById("inventory");
  table.innerHTML = "<tr><th>Item</th><th>Loc</th><th>LOT</th><th>Qty</th></tr>";
  data.forEach(r => {
    table.innerHTML += `<tr>
      <td>${r.item_code}</td>
      <td>${r.location_code}</td>
      <td>${r.lot}</td>
      <td>${r.quantity}</td>
    </tr>`;
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
