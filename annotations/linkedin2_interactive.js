function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

window.addEventListener("load", function() {
    // Target Elements to Detect and Taint
    const targets = [
        { selector: "#username", name: "Email Input" },
        { selector: "#password", name: "Password Input" },
        { selector: "#password-visibility-toggle", name: "Show Password Button" },
        { selector: "button[aria-label='Sign in']", name: "Sign In Button" }
    ];

    // Initialize independent listeners for each field
    targets.forEach(target => {
        waitForElm(target.selector).then((elm) => {
            elm.setAttribute("data-taint", "1");
            console.log(`Interactive Taint: ${target.name} found`);
        });
    });
});

