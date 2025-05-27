document.addEventListener('DOMContentLoaded', () => {
    const resultBox = document.getElementById('flip-result');
    if (resultBox) {
        resultBox.style.transform = 'scale(0)';
        setTimeout(() => {
            anime({
                targets: '#flip-result',
                scale: [0, 1],
                duration: 1000,
                easing: 'easeOutElastic(1, .8)'
            });
        }, 100);
    }
});
