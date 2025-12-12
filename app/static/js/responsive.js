
// 모바일 환경 최적화
(function() {
    console.log("Responsive UI Loaded");

    // iOS 카메라 문제 해결
    if (/iPhone|iPad/.test(navigator.userAgent)) {
        document.body.style.height = "100%";
    }
})();
