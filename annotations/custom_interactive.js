function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }
        const observer = new MutationObserver(() => {
            const candidate = document.querySelector(selector);
            if (candidate) {
                resolve(candidate);
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
}

window.addEventListener('load', function () {
    waitForElm('#pass').then((input) => {
        input.setAttribute('data-taint', '1');
    });
});

