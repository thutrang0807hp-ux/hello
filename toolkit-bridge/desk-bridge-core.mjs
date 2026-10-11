// Freelance Desk bridge: reads already-fetched jobs; never requests Upwork.
export const KEY = '__FREELANCE_DESK_BRIDGE_V1';
export const ALARM = 'freelance-desk-bridge-retry';
export function validateEndpoint(value) {
  let url;
  try { url = new URL(value); } catch { throw new Error('Dán URL nhận job từ Hồ sơ & kết nối trong Freelance Desk.'); }
  if (url.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(url.hostname) ||
      url.username || url.password || url.search || url.hash ||
      !/^\/api\/webhook\/[a-zA-Z0-9_-]{16,200}$/.test(url.pathname)) {
    throw new Error('Bản cầu nối này chỉ gửi đến Freelance Desk trên máy bạn (http://127.0.0.1 hoặc http://localhost).');
  }
  return url.href;
}
const plain = (value, max = 20000) => typeof value === 'string' ? value.replace(/<[^>]*>/g, ' ')
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&#0?39;|&apos;/g, "'").replace(/&nbsp;/g, ' ').trim().slice(0, max) : '';
const number = value => value !== null && value !== '' && value !== undefined &&
  Number.isFinite(Number(value)) && Number(value) >= 0 ? Number(value) : null;
const stamp = value => typeof value === 'string' && value && Number.isFinite(Date.parse(value)) ? new Date(value).toISOString() : '';
export function normalizeJob(job) {
  if (!job || typeof job !== 'object' || Array.isArray(job)) return null;
  const id = typeof job.ciphertext === 'string' ? job.ciphertext : '';
  const title = plain(job.title, 1000);
  if (!/^~?[a-zA-Z0-9_-]{1,199}$/.test(id) || !title) return null;
  const hourly = job.type === 'Hourly';
  const min = number(job.hourlyBudget?.min), max = number(job.hourlyBudget?.max), amount = number(job.amount?.amount);
  const budget = hourly ? (min > 0 && max > 0 && min !== max ? `$${min}–$${max}/hr` : min > 0 ? `$${min}/hr` : max > 0 ? `Tối đa $${max}/hr` : '') : amount > 0 ? `$${amount}` : '';
  const attrs = Array.isArray(job.attrs) ? job.attrs : [];
  const skills = attrs.map(a => plain(a?.prettyName || a?.prefLabel, 200)).filter(Boolean).slice(0, 100);
  return {
    id, title, url: `https://www.upwork.com/jobs/${encodeURIComponent(id)}`,
    description: plain(job.description), type: plain(job.type, 200), budget,
    skills, engagement: plain(job.engagement, 200), duration: plain(job.durationLabel || job.duration, 200),
    proposalsTier: plain(job.proposalsTier, 200),
    postedAt: stamp(job.renewedOn) || stamp(job.publishedOn) || stamp(job.createdOn),
    client: {
      rating: number(job.client?.totalFeedback), country: plain(job.client?.location?.country, 200),
      totalSpent: number(job.client?.totalSpent), totalHires: number(job.client?.totalHires),
      paymentVerified: job.client?.paymentVerificationStatus === 1 ? true : job.client?.paymentVerificationStatus === 0 ? false : null,
    },
  };
}
export function installBridge(api, request = fetch) {
  let chain = Promise.resolve();
  const serialize = action => {
    const result = chain.then(action);
    chain = result.catch(() => {});
    return result;
  };
  const load = async () => (await api.storage.local.get(KEY))[KEY] || { enabled: false, url: '', pending: [], sent: [], total: 0 };
  const store = state => api.storage.local.set({ [KEY]: state });
  const report = state => ({ enabled: !!state.enabled, configured: !!state.url, pending: state.pending?.length || 0,
    total: state.total || 0, lastSuccess: state.lastSuccess || '', error: state.error || '', rejected: state.rejected || 0, overflow: state.overflow || 0 });
  async function synchronize() {
    const state = await load();
    if (!state.enabled || !state.url) return report(state);
    try { validateEndpoint(state.url); } catch { state.enabled = false; state.error = 'URL cấu hình không hợp lệ.'; await store(state); return report(state); }
    const jobs = (await api.storage.local.get('__JOBS')).__JOBS;
    const source = Array.isArray(jobs) ? jobs : [];
    const known = new Set([...(state.sent || []), ...(state.pending || []).map(job => job.id)]);
    state.pending ||= []; state.sent ||= []; state.rejected = 0; state.overflow = 0;
    let bytes = JSON.stringify(state.pending).length * 3;
    for (const raw of source) {
      const job = normalizeJob(raw);
      if (!job) { state.rejected++; continue; }
      if (known.has(job.id)) continue;
      const size = JSON.stringify(job).length * 3;
      if (state.pending.length >= 500 || bytes + size > 4 * 1024 * 1024) { state.overflow++; continue; }
      state.pending.push(job); known.add(job.id); bytes += size;
    }
    // Persist before sending so a closed app or service-worker restart doesn't lose queued jobs.
    await store(state);
    while (state.pending.length) {
      const batch = state.pending.slice(0, 10);
      try {
        const response = await request(state.url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ event: 'new_jobs', jobs: batch }), signal: AbortSignal.timeout(10000),
          credentials: 'omit', redirect: 'error', cache: 'no-store' });
        if (!response.ok) {
          state.error = response.status === 403 ? 'URL nhận job đã sai hoặc thay đổi. Sao chép lại URL từ Freelance Desk.' : `Freelance Desk trả lỗi ${response.status}. Job vẫn được giữ để thử lại.`;
          await store(state); return report(state);
        }
        const result = await response.json();
        if (!Number.isInteger(result.created) || !Number.isInteger(result.duplicates) || result.created + result.duplicates !== batch.length) throw new Error('Invalid acknowledgement');
        state.pending.splice(0, batch.length);
        state.sent = [...new Set([...state.sent, ...batch.map(job => job.id)])].slice(-5000);
        state.total = (state.total || 0) + result.created;
        state.lastSuccess = new Date().toISOString(); state.error = '';
        await store(state);
      } catch {
        state.error = 'Chưa kết nối được. Mở Freelance Desk bằng start-windows.bat; job đang chờ sẽ tự gửi lại.';
        await store(state); return report(state);
      }
    }
    state.error = ''; await store(state); return report(state);
  }
  const safeRun = action => serialize(action).catch(() => ({ error: 'Không lưu được hàng đợi kết nối. Kiểm tra bộ nhớ tiện ích và thử lại.' }));
  api.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.__JOBS) void safeRun(synchronize);
  });
  api.alarms.onAlarm.addListener(alarm => { if (alarm.name === ALARM) void safeRun(synchronize); });
  api.runtime.onMessage.addListener((message, sender, reply) => {
    if (sender.id !== api.runtime.id || message?.target !== 'freelance-desk-bridge') return;
    safeRun(async () => {
      let state = await load();
      if (message.action === 'status') return report(state);
      if (message.action === 'stop') { state.enabled = false; await store(state); return report(state); }
      if (message.action === 'connect') {
        let url; try { url = validateEndpoint(message.url); } catch (error) { return { error: error.message }; }
        if (state.url !== url) state = { ...state, url, enabled: true, sent: [], total: 0, lastSuccess: '' };
        else state.enabled = true;
        await store(state);
        await api.alarms.create(ALARM, { periodInMinutes: 1 });
        return synchronize();
      }
      if (message.action === 'sync') return synchronize();
      return { error: 'Thao tác không hợp lệ.' };
    }).then(reply);
    return true;
  });
  void safeRun(async () => {
    const state = await load();
    if (state.enabled) { await api.alarms.create(ALARM, { periodInMinutes: 1 }); return synchronize(); }
  });
  return { synchronize: () => safeRun(synchronize), status: () => safeRun(async () => report(await load())) };
}
