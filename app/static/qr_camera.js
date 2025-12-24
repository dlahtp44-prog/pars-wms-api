let scanner;

async function startScan(){
  scanner = new Html5Qrcode("reader");
  const cams = await Html5Qrcode.getCameras();
  const back = cams.find(c=>c.label.toLowerCase().includes("back")) || cams[0];

  scanner.start(back.id,{fps:10,qrbox:250}, async text=>{
    scanner.stop();
    const res = await fetch("/api/qr/process",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(Object.fromEntries(new URLSearchParams(text)))
    });
    const d = await res.json();
    document.getElementById("result").innerHTML =
      d.type==="LOCATION"
        ? `<h3>📍 ${d.location}</h3>` + d.items.map(i=>`
            <div>${i.item_code} / ${i.lot_no} / ${i.qty}</div>
          `).join("")
        : "처리 실패";
  });
}
