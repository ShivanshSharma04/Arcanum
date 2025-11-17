chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === 'arcanum-interaction-leak') {
    chrome.storage.local.set(
      {
        interaction_leak: {
          payload: message.payload,
          timestamp: Date.now()
        }
      },
      () => {
        sendResponse({ status: 'stored' });
      }
    );
    return true;
  }
  return false;
});

