# Freelance Desk — instructions for coding agents

Read `DOC-TRUOC-KHI-SUA.md` first, then the relevant source and README. This project has established behavior; do not rebuild it from scratch or infer current behavior from an old demo. The user's explicit new requirements take precedence over these defaults.

- Python stdlib + SQLite backend, vanilla JS frontend. Preserve the stack unless a change actually requires otherwise.
- UI and AI explanation output must be Vietnamese. Keep ordinary user flows concise; advanced configuration is collapsed by default.
- Job stars/filtering are local rules, without AI calls. Job AI is explicit, cached, and collapsed inside the single "Phân tích công việc" modal. Never restore hover-triggered or background AI scoring.
- Preserve batch clearing of job notifications when opening the job view and automatic unread favicon counts for newly received jobs.
- Gmail reads Upwork message notifications only by application filter; its OAuth readonly scope can still read other Gmail mail. Do not misrepresent the permission. Link by known room mapping or explicit user selection, not a guessed name. Never equate a message with a contract.
- Preserve existing records, descriptions, proposals and SQLite migrations. Do not delete `data/` to fix an error. Tests should use an isolated temporary `FREELANCE_DATA_DIR` and mocked provider/notification responses.
- Keep secrets and user data out of logs, screenshots, Git and ZIP. `.env.example` may contain names/defaults only. Do not invoke real AI, send Slack/Telegram/email messages, or perform Upwork actions just to validate a change.
- Check relevant Python/JS tests and functional UI behavior. Playwright smoke scripts assume Linux Chromium at `/usr/bin/chromium`; account for platform differences without bypassing managed browser policy.
- Keep all required runtime files in the release ZIP. New frontend assets need a static route and HTML inclusion. Updates require server restart plus browser reload, not just replacing files while the old process runs.
- Use the existing checkout; a worktree is unnecessary unless the user requests one. Report what was verified and what still needs real account or Windows validation.

- Persistent storage is unified by data_store.py: Windows defaults to LOCALAPPDATA/FreelanceDesk/data; explicit FREELANCE_DATA_DIR wins, relative paths are source-root-relative. Legacy data is copied only into an empty destination, originals retained. Preserve migration safety and Gmail refresh tokens when saving unchanged OAuth credentials.

- Windows storage can be selected using choose-data-windows.bat after stopping the app. Close SQLite connections explicitly before directory renames; transaction context managers alone do not release Windows handles. Exclude location-pointer JSON from release archives.

- Desktop background start/stop must only manage the authenticated local instance using its private control token; never kill arbitrary Python processes. Keep desktop-server.json and logs out of artifacts. Stop the background server before updates/storage changes.

- uninstall_desk.py is destructive only after its local review/confirmation. Never execute it against real repo/user data as a test. Validate the exact allowlist, stop ownership, no recursive unrelated-folder deletion, and symlink protection in temporary fixtures. Remote Google grants and Chrome extensions are not removed by local uninstall.

- User explicitly requested automatic next-action understanding for linked customer emails. mail_actions.py may call AI on new message content while its persisted toggle is enabled; this is separate from job scoring, which remains manual. Cache results, preserve manual edits and customer groups, and never send replies or claim contracts automatically. Tests must mock the provider.

- Chrome tab/favicon now combine job unread count with union(unread mail, unresolved mail). Title labels jobs/mail separately; never double-count a mail in both states. Job-view batch clear must not clear mail attention. Read linked mail clears its count; read unresolved mail still requires linking.

- Active contracts support manual paused stage + reason/note. Preserve active group and pause state across mail updates; no automatic Ghost judgment or resume. Suppress automatic silence-only priority for paused clients, but retain explicit follow-up dates.

- Client stage signals are local/manual. Autoarchive talk/testing only from explicit clientTestSentDate after 14 days without reply on/after sent date. Active contracts never autoarchive. Preserve inquiry-date rule and reset stale timers on reopening.

- CRM cards default collapsed using native details/summary. Keep status/unread/test deadline visible, preserve expansion across refresh and focus/drafts while editing. UI smoke tests must explicitly expand cards before editing.

- Pause reason and optional note share a nested disclosure, closed by default and after successful save. Failed saves preserve draft. Keep the saved reason visible in its summary.

- Desktop wrapper is Windows-only pywebview/Edge Chromium + pystray, reusing private-token local backend/storage. Preserve external-browser Google OAuth and its cookie/state checks. Venv/profile cache never belong in release ZIP. Explicit Exit stops; close hides only when tray is available. Do not claim Windows GUI was verified from Linux mocks.

- Desktop failures must be stage-specific and redacted. Check .NET/WebView2 before startup; reject MSHTML fallback. Repair only executes valid Microsoft-signed WebView2 bootstrapper, no global execution-policy changes. Never include desktop-diagnostic.txt in releases/handoffs.

- Rerunning desktop installation must probe/reuse a healthy .desktop-venv, never recreate its running pythonw.exe. Preserve partial/invalid environments and report instead of deleting. Permission errors are not automatically network errors.
