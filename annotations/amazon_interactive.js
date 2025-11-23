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
        { id: "#ya-myab-address-add-link", name: "Add Address Button" },
        { id: "#address-ui-widgets-enterAddressFullName", name: "Full Name" },
        { id: "#address-ui-widgets-enterAddressPhoneNumber", name: "Phone Number" },
        { id: "#address-ui-widgets-enterAddressLine1", name: "Address Line 1" },
        { id: "#address-ui-widgets-enterAddressCity", name: "City" },
        { id: "#address-ui-widgets-enterAddressPostalCode", name: "Zip Code" },
        { id: "#address-ui-widgets-form-submit-button", name: "Submit Button" }
    ];

    // Initialize independent listeners for each field
    targets.forEach(target => {
        waitForElm(target.id).then((elm) => {
            elm.setAttribute("data-taint", "1");
            console.log(`Interactive Taint: ${target.name} found`);
        });
    });
});
