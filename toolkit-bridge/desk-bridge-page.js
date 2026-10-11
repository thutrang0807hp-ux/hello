const $ = id => document.getElementById(id);
let busy = false;
async function command(action, extra = {}) {
  return chrome.runtime.sendMessage({ target: 'freelance-desk-bridge', action, ...extra });
}
function paint(value) {
  if (!value) { $('error').textContent = 'Cầu nối chưa phản hồi. Vào chrome://extensions và bấm Reload của bản Toolkit kết nối.'; return; }
  if ('enabled' in value) {
    $('status').textContent = value.enabled ? 'Kết nối đã bật' : 'Kết nối đang tắt';
    $('total').textContent = value.total || 0; $('pending').textContent = value.pending || 0;
    $('time').textContent = value.lastSuccess ? `Gửi thành công gần nhất: ${new Date(value.lastSuccess).toLocaleString('vi-VN')}` : 'Chưa có lần gửi thành công.';
    $('notice').textContent = [value.rejected ? `${value.rejected} job trong bộ nhớ thiếu ID hoặc tiêu đề nên chưa gửi.` : '', value.overflow ? `Hàng đợi đầy: ${value.overflow} job hiện có chưa vào hàng đợi. Mở web để giải phóng hàng đợi rồi gửi lại.` : ''].filter(Boolean).join(' ');
    if (value.configured && !$('endpoint').value) $('endpoint').placeholder = 'Đã lưu URL. Dán URL mới khi muốn đổi kết nối.';
  }
  $('error').textContent = value.error || '';
}
async function act(action) {
  if (busy) return; busy = true;
  document.querySelectorAll('button').forEach(button => button.disabled = true);
  try { paint(await command(action, action === 'connect' ? { url: $('endpoint').value.trim() } : {})); }
  catch { $('error').textContent = 'Không liên lạc được với cầu nối. Thử Reload tiện ích và mở lại trang này.'; }
  finally { busy = false; document.querySelectorAll('button').forEach(button => button.disabled = false); }
}
for (const action of ['connect', 'sync', 'stop']) $(action).addEventListener('click', () => act(action));
act('status');
setInterval(() => { if (!busy) act('status'); }, 5000);
