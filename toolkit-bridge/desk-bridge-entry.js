const link = document.createElement('a');
link.textContent = '↗ Kết nối Freelance Desk';
link.href = chrome.runtime.getURL('desk-bridge.html');
link.target = '_blank'; link.rel = 'noopener';
link.style.cssText = 'position:fixed;left:16px;bottom:16px;z-index:10000;padding:12px 16px;border-radius:12px;background:#6945bd;color:#fff;text-decoration:none;font:600 13px Arial;box-shadow:0 4px 18px #0003';
document.body.append(link);
