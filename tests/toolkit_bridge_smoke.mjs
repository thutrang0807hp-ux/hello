// Run via toolkit_bridge_smoke.py: exercises the bridge against the actual HTTP importer.
import assert from 'node:assert/strict';
import { installBridge, KEY } from '../toolkit-bridge/desk-bridge-core.mjs';
const url = process.env.TOOLKIT_TEST_WEBHOOK;
assert.ok(url);
const data = { __JOBS: [{ ciphertext: '~0123456789abcdef', title: 'Bridge import test', type: 'Hourly',
  hourlyBudget: { min: 25, max: 40 }, description: 'A full job description. '.repeat(100),
  publishedOn: '2026-10-10T15:30:00Z', attrs: [{ prettyName: 'Figma' }],
  client: { location: { country: 'United States' }, totalFeedback: 4.9, totalHires: 5, totalSpent: 10000 } }] };
let listener;
const api = { storage: { local: {
  get: async key => ({ [key]: structuredClone(data[key]) }),
  set: async values => { Object.assign(data, structuredClone(values)); },
}, onChanged: { addListener() {} } }, alarms: { create: async()=>{}, onAlarm:{addListener(){}} },
  runtime:{id:'test',onMessage:{addListener(callback){listener=callback;}}} };
let offline = true;
installBridge(api, (...args) => { if (offline) throw new Error('App closed'); return fetch(...args); });
const send = (action, extra = {}) => new Promise(resolve => listener({ target:'freelance-desk-bridge', action, ...extra },{id:'test'},resolve));
assert.equal((await send('connect',{url})).pending,1);
offline=false;
let status=await send('sync');assert.equal(status.pending,0);assert.equal(status.total,1);
// Replays from a restarted service-worker or a lost acknowledgement are safely deduplicated by the server.
data[KEY].sent=[];
status=await send('sync');assert.equal(status.total,1);assert.equal(status.pending,0);
console.log('PASS real app import, offline retry, server-side deduplication');
