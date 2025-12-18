function scan() {
  const v = document.getElementById("qr").value.trim();

  if (!v) {
    alert("QR 값을 입력하세요");
    return;
  }

  location.href = "/qr-page?item=" + encodeURIComponent(v);
}

