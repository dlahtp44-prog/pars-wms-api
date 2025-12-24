let moveStep = 1; 
let moveInfo = { from: '', item: '', lot: '', maxQty: 0 };

async function onScanSuccess(decodedText) {
    if (moveStep === 1) {
        // [1단계] 출발지 QR 스캔
        const res = await fetch(`/api/qr/location/${decodedText}`);
        const items = await res.json();
        if (items.length > 0) {
            moveInfo.from = decodedText;
            displayItemSelection(items); // 목록 표시 함수 (UI)
            moveStep = 2;
            document.getElementById('qr-status').innerText = "이동할 품목을 선택하세요.";
        } else {
            alert("이 위치에 재고가 없습니다.");
        }
    } else if (moveStep === 3) {
        // [3단계] 도착지 QR 스캔
        const qty = document.getElementById('moveQty').value;
        const res = await fetch('/api/move/manual', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                warehouse: "기본창고", from_location: moveInfo.from, to_location: decodedText,
                item_code: moveInfo.item, lot_no: moveInfo.lot, qty: parseFloat(qty)
            })
        });
        if(res.ok) { alert("이동 완료!"); location.reload(); }
    }
}

function selectItem(code, lot, qty) {
    moveInfo.item = code; moveInfo.lot = lot; moveInfo.maxQty = qty;
    moveStep = 3;
    document.getElementById('qr-status').innerText = "마지막으로 도착지 QR을 스캔하세요.";
}
