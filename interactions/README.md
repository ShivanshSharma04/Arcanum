# Interaction Scripts

The JSON files in this directory define optional, replayable user interactions
that the Selenium harness can execute after a page finishes loading.

Each file follows this schema:

```json
{
  "target": "{page_key}",
  "preload_wait_ms": 1000,
  "steps": [
    {
      "action": "type | click | wait | execute_script",
      "strategy": "css | xpath | id | name | tag", // required for click/type actions
      "selector": "CSS/XPath selector string",
      "text": "Only for type actions",
      "clear": true,
      "timeout_ms": 5000
    }
  ]
}
```

* `target` matches the page identifier used in `Test_Cases/Custom_Test.py`
  (for example: `amazon_address`, `fb_post`, `custom_interactive`).
* `preload_wait_ms` adds a short delay before executing the first step.
* `steps` are executed sequentially:
  * `type` – waits for an element, optionally clears it, and sends keys.
  * `click` – waits for an element and triggers `.click()`.
  * `execute_script` – runs the provided JavaScript in the page context.
  * `wait` – sleeps for the specified number of milliseconds.

When no interaction file exists for a page, the harness simply skips the
interaction phase, keeping the previous passive workflow intact.

