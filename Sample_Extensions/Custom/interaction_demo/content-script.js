const INTERACTION_EVENT = 'arcanumUserFlowComplete';

function readTaintedValue() {
  const sensitiveInput = document.querySelector('#pass[data-taint="1"]');
  if (!sensitiveInput) {
    return null;
  }
  return sensitiveInput.value || sensitiveInput.textContent || '';
}

function emitLeak() {
  const payload = readTaintedValue();
  if (!payload) {
    return;
  }
  chrome.runtime.sendMessage({
    type: 'arcanum-interaction-leak',
    payload
  });
}

function registerInteractionHooks() {
  window.addEventListener(INTERACTION_EVENT, emitLeak);
}

registerInteractionHooks();

