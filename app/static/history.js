// app/static/history.js (예시)
async function loadHistory() {
    const response = await fetch('/api/history');
    const data = await response.json();
    const tbody = document.getElementById('history-tbody');
    
    if (!tbody) return;
    tbody.innerHTML = ''; // 기존 내용 삭제

    data.forEach(h => {
        const row = `<tr>
            <td>${h.created_at.split('T')[0]}</td>
            <td><span class="badge ${h.tx_type}">${h.tx_type}</span></td>
            <td>${h.item_code}</td>
            <td>${h.qty}</td>
            <td>${h.location || ''} ${h.to_location ? '→ ' + h.to_location : ''}</td>
            <td><button onclick="doRollback(${h.id})">롤백</button></td>
        </tr>`;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

document.addEventListener('DOMContentLoaded', loadHistory);
