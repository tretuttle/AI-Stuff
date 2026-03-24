---
description: Check browser-capture plugin health — verify dependencies, Chromium browser, paths, and configuration are all working correctly.
---

# Browser Capture Health Check

Run the health check to verify all dependencies and configuration:

```bash
NODE_PATH="${CLAUDE_PLUGIN_DATA}/node_modules" \
PLAYWRIGHT_BROWSERS_PATH="${CLAUDE_PLUGIN_DATA}" \
node "${CLAUDE_PLUGIN_ROOT}/scripts/health-check.js"
```

If any checks fail, report the failures to the user with the suggested fixes.

If all checks pass, confirm the plugin is ready and report the summary.
