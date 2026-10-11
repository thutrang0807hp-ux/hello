# Bridge for the uploaded Chrome Web Store Toolkit 1.6.0

The installed build has no native webhook UI. This additive bridge watches `chrome.storage.local.__JOBS`, normalizes already-fetched job data, and POSTs it to the existing Freelance Desk importer on localhost. It never requests Upwork and does not read sync settings, cookies or AI keys.

The original background bundle is preserved with one appended module import. Original content scripts, request modifiers, job fetcher, scheduler and compiled libraries stay byte-identical. An extra module adds a connection-page link to the original options page. The manifest icon popup and extension options open the connection page directly; its Toolkit link opens the original job/settings UI in a separate tab. The manifest has a distinct name and ID (Web Store key/update URL removed), plus HTTP localhost permissions. It does not migrate data from another extension's storage.

## Package

```sh
python toolkit-bridge/package.py /path/to/original/1.6.0_0 /tmp/bridge-output
```

The input stays unchanged. SHA-256 checks guard against patching a different bundle; the output includes provenance and GPL-3.0 license. Corresponding upstream source is identified by the shipped Sentry release ID `4be0325640df585fb9030a5ddffa756ea0effce0`. `downloads/Toolkit-Installed-Build-Source.zip` contains that upstream source plus these bridge/package files.

## Validation

```sh
node --test tests/toolkit_bridge.test.mjs
python tests/toolkit_bridge_smoke.py
```

Six tests cover normalization, destination restrictions, deduplication, durable offline retry across worker restart, failed acknowledgements, stopping, changing endpoints, concurrent sends, malformed jobs and sender validation. The smoke test exercises actual app HTTP import and stored description, budget, client and source date. No live Upwork, AI, Slack or Telegram credentials are used.

The browser in this cloud workspace is managed with `ExtensionInstallBlocklist: ["*"]`; unpacked-extension runtime testing is blocked. Browser policy was left unchanged. Manual Chrome installation and actual Upwork-feed reception remain to be verified on the user's Windows machine; no Upwork account-safety guarantee is implied.

## Queue behavior

Pending payloads persist before sending. Only acknowledged jobs are marked sent. The importer deduplicates retries when a response is lost. A separate retry alarm runs every minute without altering Toolkit's fetch alarm. Each request has at most ten jobs and a ten-second timeout. Pending queue: 500 jobs / conservatively estimated 4 MB; overflow is visible in the connection page. Full cached descriptions are retained up to the importer's 20,000-character limit. Delivered-ID history is capped at 5,000; server deduplication also protects older replays. Changing destination retains queued payloads and resets delivered-ID tracking.

Only explicit `http://localhost` or `http://127.0.0.1` token endpoints are accepted. No redirects, embedded credentials, query strings or fragments; requests omit credentials. Endpoint tokens stay in private extension storage and are not included in status/error responses. Disable other Toolkit editions while this copy is active.
