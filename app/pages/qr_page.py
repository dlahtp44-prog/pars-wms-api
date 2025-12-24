from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr-page", response_class=HTMLResponse)
async def qr_page(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>QR 창고 관리</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/html5-qrcode"></script>
        <style>
            #reader { width: 100%; border: 2px solid #007bff; border-radius: 10px; overflow: hidden; }
            .step-active { background-color: #e7f3ff; border-left: 5px solid #007bff; }
            .item-card { cursor: pointer; transition: 0.2s; }
            .item-card:hover { background-color: #f8f9fa; }
        </style>
    </head>
    <body class="bg-light">
        <div class="container py-3">
            <h4 class="mb-3 text-center">📱 QR 재고 이동</h4>
            
            <div id="reader" class="mb-3"></div>
            
            <div id="status-card" class="card mb-3">
                <div class="card-body">
                    <h6 id="current-step-text" class="card-title text-primary">단계 1: 출발지 QR을 스캔하세요</h6>
                    <p id="move-info" class="card-text small text-muted">스캔 대기 중...</p>
                </div>
            </div>

            <div id="item-selection" class="list-group shadow-sm" style="display:none;">
                </div>
        </div>

        <script>
            let currentStep = 1;
            let moveData = { from_location: '', to_location: '', item_code: '', lot_no: '', qty: 0 };

            function onScanSuccess(decodedText) {
                if (currentStep === 1) {
                    processSourceLocation(decodedText);
                } else if (currentStep === 3) {
                    processTargetLocation(decodedText);
                }
            }

            async function processSourceLocation(loc) {
                const res = await fetch(`/api/qr/location/${loc}`);
                const items = await res.json();
                if (items.length > 0) {
                    moveData.from_location = loc;
                    document.getElementById('move-info').innerText = `출발지: ${loc}`;
                    renderItemList(items);
                    nextStep(2, "단계 2: 이동할 품목을 선택하세요");
                } else {
                    alert("해당 위치에 재고가 없습니다.");
                }
            }

            function renderItemList(items) {
                const container = document.getElementById('item-selection');
                container.style.display = 'block';
                container.innerHTML = items.map(i => `
                    <button class="list-group-item list-group-item-action item-card" onclick="selectItem('${i.item_code}', '${i.lot_no}', ${i.qty})">
                        <strong>${i.item_name}</strong><br>
                        <span class="small">코드: ${i.item_code} | LOT: ${i.lot_no}</span><br>
                        <span class="badge bg-info">현재고: ${i.qty}</span>
                    </button>
                `).join('');
            }

            function selectItem(code, lot, maxQty) {
                const qty = prompt(`이동할 수량을 입력하세요 (최대 ${maxQty})`, maxQty);
                if (!qty || qty <= 0) return;
                
                moveData.item_code = code;
                moveData.lot_no = lot;
                moveData.qty = qty;
                
                document.getElementById('item-selection').style.display = 'none';
                document.getElementById('move-info').innerHTML += `<br>품목: ${code} (${qty}개)`;
                nextStep(3, "단계 3: 도착지 QR을 스캔하세요");
            }

            async function processTargetLocation(loc) {
                if (loc === moveData.from_location) {
                    alert("출발지와 도착지가 같습니다!");
                    return;
                }
                moveData.to_location = loc;
                const res = await fetch('/api/qr/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(moveData)
                });
                if (res.ok) {
                    alert("✅ 이동 처리가 완료되었습니다!");
                    location.reload();
                }
            }

            function nextStep(step, text) {
                currentStep = step;
                document.getElementById('current-step-text').innerText = text;
            }

            const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
            scanner.render(onScanSuccess);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
