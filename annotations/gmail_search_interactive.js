document.body.dataset.annotationLoaded = "true";

function taintSearchBar() {
    const search = document.querySelector('input[aria-label="Search mail"]');
    if (search) {
        search.setAttribute('data-taint', '1');
        console.log("Tainted Gmail search bar");
        return true;
    }
    return false;
}

// Keep trying until Gmail loads the real search box.
const interval = setInterval(() => {
    if (taintSearchBar()) clearInterval(interval);
}, 300);

// Re-taint it if Gmail re-renders the DOM (which it does frequently)
const obs = new MutationObserver(taintSearchBar);
obs.observe(document.body, { childList: true, subtree: true });