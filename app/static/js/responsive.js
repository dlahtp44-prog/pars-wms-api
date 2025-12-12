(function () {
    console.log("Responsive UI Loaded");

    // iOS 감지 함수 (iPadOS 포함)
    const isIOS = () => {
        return /iPhone|iPad|iPod/.test(navigator.userAgent) ||
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    };

    if (isIOS()) {
        console.log("iOS device detected — applying viewport fix.");

        // ① 100vh 문제 해결 (iOS에서 주소창 때문에 100vh 깨짐)
        const setVh = () => {
            document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
        };
        setVh();
        window.addEventListener('resize', setVh);

        // ② body 높이 고정
        document.body.style.height = "calc(var(--vh, 1vh) * 100)";

        // ③ 카메라 input 터치 시 스크롤 튀는 현상 방지
        document.body.style.position = "fixed";
        document.body.style.width = "100%";
    }
})();
