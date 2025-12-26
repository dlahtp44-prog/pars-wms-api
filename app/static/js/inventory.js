async function loadInventory() {
  const res = await fetch("/api/inventory");
  const data = await res.json();

  const tbody = document.getElementById("inventoryBody");
  tbody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = "<tr><td colspan='4'>재고 없음</td></tr>";
    return;
  }

  data.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.item_code}</td>
      <td>${r.location_code}</td>
      <td>${r.lot}</td>
      <td style="text-align:right;">${r.quantity}</td>
    `;
    tbody.appendChild(tr);
  });
}
