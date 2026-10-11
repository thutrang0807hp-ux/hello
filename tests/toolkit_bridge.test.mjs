import test from 'node:test';
import assert from 'node:assert/strict';
import { installBridge, normalizeJob, validateEndpoint, KEY, ALARM } from '../toolkit-bridge/desk-bridge-core.mjs';
const URL = 'http://127.0.0.1:8000/api/webhook/test-token-1234567890';
const job = (id = '~012345') => ({ ciphertext: id, title: 'UI &amp; UX', description: '<p>Design dashboard</p>\nSecond paragraph',
  type: 'Fixed-price', amount: { amount: '800' }, attrs: [{ prettyName: 'Figma' }], renewedOn: '2026-10-10T12:00:00Z',
  client: { totalFeedback: 4.9, location: { country: 'United States' }, totalSpent: 1000, totalHires: 3, paymentVerificationStatus: 1 },
  cookie: 'must not send', apiKey: 'must not send' });
const response = (count, status = 200) => ({ ok: status === 200, status, json: async () => ({ created: count, duplicates: 0 }) });
function mock(data = {}) {
  const reads = [], handlers = { change: [], alarm: [], message: [] };
  const api = {
    storage: { local: {
      get: async key => { reads.push(key); return { [key]: structuredClone(data[key]) }; },
      set: async values => { Object.assign(data, structuredClone(values)); },
    }, onChanged: { addListener: callback => handlers.change.push(callback) } },
    alarms: { onAlarm: { addListener: callback => handlers.alarm.push(callback) }, create: async () => {} },
    runtime: { id: 'test-extension', onMessage: { addListener: callback => handlers.message.push(callback) } },
  };
  const send = (action, extra = {}, sender = { id: api.runtime.id }) => new Promise(resolve => {
    const result = handlers.message[0]({ target: 'freelance-desk-bridge', action, ...extra }, sender, resolve);
    if (!result) resolve(undefined);
  });
  return { api, data, reads, handlers, send };
}
test('accept only local token endpoint; reject external hosts, credentials, redirect parameters', () => {
  assert.equal(validateEndpoint(URL), URL);
  assert.match(validateEndpoint(URL.replace('127.0.0.1', 'localhost')), /localhost/);
  for (const bad of ['https://evil.example/api/webhook/test-token-1234567890', URL.replace('127.0.0.1','127.0.0.1.evil.example'),
    URL + '?next=https://evil.example', URL + '#fragment', URL.replace('127.0.0.1', 'name:pass@127.0.0.1'), 'http://localhost/api/settings']) assert.throws(() => validateEndpoint(bad));
});
test('normalize actual cache fields, keep full description, unknown date and rating remain unknown', () => {
  const raw = job(); raw.description = 'Long paragraph '.repeat(200);
  const value = normalizeJob(raw);
  assert.equal(value.description, raw.description.trim()); assert.equal(value.title, 'UI & UX');
  assert.equal(value.budget, '$800'); assert.equal(value.client.totalHires, 3);
  assert.equal(value.postedAt, '2026-10-10T12:00:00.000Z');
  assert.equal(value.cookie, undefined); assert.equal(value.apiKey, undefined);
  const unknown = normalizeJob({ ciphertext: 'other', title: 'Other', type: 'Hourly', hourlyBudget: { min: 20, max: 35 } });
  assert.equal(unknown.budget, '$20–$35/hr'); assert.equal(unknown.postedAt, ''); assert.equal(unknown.client.rating, null);
  assert.equal(normalizeJob({ title: 'No ID' }), null);
});
test('connect sends cached jobs; repeated sync and seen-state changes never duplicate; no secret reads', async () => {
  const m = mock({ __JOBS: [job()], __STATE: { apiKey: 'private' } }); const sent = [];
  installBridge(m.api, async (url, options) => { sent.push({ url, options }); return response(JSON.parse(options.body).jobs.length); });
  const status = await m.send('connect', { url: URL });
  assert.equal(status.total, 1); assert.equal(status.pending, 0); assert.equal(sent.length, 1);
  await m.send('sync'); m.data.__JOBS[0].__isSeen = true;
  m.handlers.change[0]({ __JOBS: {} }, 'local'); await m.send('status');
  assert.equal(sent.length, 1); assert.ok(m.reads.every(key => ['__JOBS', KEY].includes(key)));
  const payload = JSON.parse(sent[0].options.body);
  assert.equal(payload.event, 'new_jobs'); assert.equal(payload.jobs[0].description, 'Design dashboard \nSecond paragraph');
  assert.equal(sent[0].options.redirect, 'error'); assert.equal(sent[0].options.credentials, 'omit');
  assert.equal(status.url, undefined);
});
test('offline queue survives service-worker restart and removed source job; retry alarm flushes it', async () => {
  const m = mock({ __JOBS: [job('first')] });
  installBridge(m.api, async () => { throw new Error('Offline'); });
  const offline = await m.send('connect', { url: URL });
  assert.equal(offline.pending, 1); assert.match(offline.error, /Chưa kết nối/);
  const restarted = mock(m.data); restarted.data.__JOBS = [job('second')]; const received = [];
  installBridge(restarted.api, async (_, options) => { const batch = JSON.parse(options.body).jobs; received.push(...batch); return response(batch.length); });
  const status = await restarted.send('status');
  assert.deepEqual(received.map(j => j.id), ['first', 'second']); assert.equal(status.pending, 0);
  restarted.data.__JOBS = [job('third')]; restarted.handlers.alarm[0]({ name: ALARM });
  assert.equal((await restarted.send('status')).total, 3);
});
test('403 and invalid acknowledgements keep queue; stop prevents sends and endpoint change preserves queue', async () => {
  const m = mock({ __JOBS: [job('queued')] }); installBridge(m.api, async () => response(0, 403));
  const denied = await m.send('connect', { url: URL }); assert.equal(denied.pending, 1); assert.match(denied.error, /URL/);
  await m.send('stop'); m.data.__JOBS = [job('new')];
  assert.equal((await m.send('sync')).pending, 1);
  await m.send('connect', { url: URL.replace(':8000', ':8001') });
  assert.deepEqual(m.data[KEY].pending.map(j => j.id), ['queued', 'new']);
  const other = mock({ __JOBS: [job()] }); installBridge(other.api, async () => ({ ok: true, json: async () => ({ ok: true }) }));
  assert.equal((await other.send('connect', { url: URL })).pending, 1);
});
test('concurrent sync serialized, malformed jobs skipped, no foreign extension commands', async () => {
  const m = mock({ __JOBS: [job(), { title: 'No ID' }, job('next')] }); let calls = 0;
  installBridge(m.api, async (_, options) => { calls++; return response(JSON.parse(options.body).jobs.length); });
  await Promise.all([m.send('connect', { url: URL }), m.send('sync'), m.send('sync')]);
  assert.equal(calls, 1); assert.equal((await m.send('status')).rejected, 1);
  assert.equal(await m.send('stop', {}, { id: 'foreign' }), undefined);
  assert.equal((await m.send('status')).enabled, true);
});
