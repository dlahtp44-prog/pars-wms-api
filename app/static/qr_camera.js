navigator.mediaDevices.getUserMedia({
  video: { facingMode: "environment" }
})
.then(stream => {
  const video = document.getElementById("video");
  if (video) {
    video.srcObject = stream;
    video.play();
  }
})
.catch(err => {
  alert("카메라 접근 실패: " + err);
});
