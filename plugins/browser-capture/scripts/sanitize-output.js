#!/usr/bin/env node
/**
 * PostToolUse hook: sanitize capture output
 *
 * Prevents binary/image data from leaking into the conversation context.
 * When capture.js output contains data URIs or base64 blobs, this hook
 * truncates them to prevent the image-poisoning bug where Claude Code's
 * terminal integration embeds malformed images that break the API.
 *
 * Reads hook input from stdin (JSON), outputs additionalContext if needed.
 */

let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);

    // Only care about Bash tool results
    if (!data.tool_name || data.tool_name !== 'Bash') {
      process.exit(0);
    }

    const stdout = data.tool_result?.stdout || '';
    const stderr = data.tool_result?.stderr || '';
    const combined = stdout + stderr;

    // Check if this is a capture.js invocation
    if (!combined.includes('capture.js') && !combined.includes('browser-capture')) {
      process.exit(0);
    }

    // Detect dangerous content patterns that could poison the conversation
    const hasDataUri = /data:[^;]+;base64,[A-Za-z0-9+/=]{100,}/.test(combined);
    const hasBinaryBlob = /[\x00-\x08\x0e-\x1f]{10,}/.test(combined);
    const hasSvgInline = /<svg[^>]*>[\s\S]{500,}<\/svg>/i.test(combined);

    if (hasDataUri || hasBinaryBlob || hasSvgInline) {
      // Inject a warning so the agent knows to avoid piping this content
      const warning = JSON.stringify({
        additionalContext: '[browser-capture] Warning: capture output contains binary/image data. ' +
          'Do NOT pipe _metadata.json or captured files through stdout. ' +
          'Use the capture-analyst agent or read files individually with the Read tool. ' +
          'Piping binary content through stdout can poison the conversation context.'
      });
      process.stdout.write(warning + '\n');
    }
  } catch {
    // Malformed input — exit silently
  }
  process.exit(0);
});
