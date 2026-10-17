// Idempotent visual jobs survive dropped HTTP requests and page reloads.
const TERMINAL = new Set(['completed', 'failed', 'cancelled']);
const keyFor = (api, sessionId) => `aceit_visual_job:${api}:${sessionId}`;
const storeFor = () => { try { return globalThis.localStorage; } catch { return null; } };
export function pendingVisualJob(api, sessionId) {
  try { return JSON.parse(storeFor()?.getItem(keyFor(api, sessionId)) || 'null'); } catch { return null; }
}
function remember(api, sessionId, value) {
  try { storeFor()?.setItem(keyFor(api, sessionId), JSON.stringify(value)); } catch { /* Generation still works without storage. */ }
}
function forget(api, sessionId, requestId) {
  try { if (pendingVisualJob(api, sessionId)?.request_id === requestId) storeFor()?.removeItem(keyFor(api, sessionId)); } catch {}
}
const abortError = () => Object.assign(new Error('Visual generation was stopped.'), { name: 'AbortError' });
const wait = (ms, signal) => new Promise((resolve, reject) => {
  if (signal?.aborted) { reject(abortError()); return; }
  const stopped = () => { clearTimeout(timer); reject(abortError()); };
  const timer = setTimeout(() => { signal?.removeEventListener('abort', stopped); resolve(); }, ms);
  signal?.addEventListener('abort', stopped, { once: true });
});
async function http(api, path, { method = 'GET', body, signal, refreshed = false } = {}) {
  if (signal?.aborted) throw abortError();
  const controller = new AbortController();
  const stop = () => controller.abort();
  signal?.addEventListener('abort', stop, { once: true });
  const timer = setTimeout(stop, 15000);
  try {
    const response = await fetch(api + path, { method, credentials: 'include', signal: controller.signal,
      headers: { 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) });
    if (response.status === 401 && !refreshed) {
      await http(api, '/auth/refresh', { method: 'POST', body: {}, signal, refreshed: true });
      return await http(api, path, { method, body, signal, refreshed: true });
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail;
      const error = new Error(typeof detail === 'string' ? detail : detail?.message || `The visual service returned HTTP ${response.status}.`);
      error.status = response.status; error.retryable = response.status === 408 || response.status === 429 || response.status >= 500;
      if (response.status === 401) error.code = 'SESSION_EXPIRED';
      throw error;
    }
    if (!data || typeof data.status !== 'string') {
      // auth/refresh returns user/session JSON instead of a job.
      if (path === '/auth/refresh') return data;
      throw Object.assign(new Error('The visual service returned an unreadable status.'), { retryable: true });
    }
    return data;
  } catch (error) {
    if (signal?.aborted) throw abortError();
    if (!error.status) error.retryable = true;
    throw error;
  } finally {
    clearTimeout(timer); signal?.removeEventListener('abort', stop);
  }
}
export async function runVisualJob({ api, sessionId, content, signal, onUpdate, onIdentity, pollMs = 1000 }) {
  const saved = pendingVisualJob(api, sessionId);
  const identity = saved?.content === content ? saved : {
    request_id: globalThis.crypto.randomUUID(), content, session_id: sessionId, job_id: null,
  };
  remember(api, sessionId, identity); onIdentity?.(identity);
  let failures = 0, lastSignature = '', reconnectingSince = 0;
  for (;;) {
    if (signal?.aborted) throw abortError();
    let job;
    try {
      job = identity.job_id
        ? await http(api, '/chat/visual-jobs/' + encodeURIComponent(identity.job_id), { signal })
        : await http(api, '/chat/sessions/' + encodeURIComponent(sessionId) + '/visual-jobs', {
            method: 'POST', body: { request_id: identity.request_id, content }, signal });
      failures = 0; reconnectingSince = 0;
    } catch (error) {
      if (error.status === 404 && identity.job_id) {
        identity.job_id = null; remember(api, sessionId, identity); continue;
      }
      if (signal?.aborted || !error.retryable) throw error;
      reconnectingSince ||= Date.now(); failures++;
      onUpdate?.({ status: 'reconnecting', job_id: identity.job_id, request_content: content });
      if (Date.now() - reconnectingSince > 60000) {
        error.visualJobPending = true;
        error.message = 'The connection is unavailable. Your visual is kept on the server; Retry reconnects to the same request.';
        throw error;
      }
      await wait(Math.min(5000, 500 * 2 ** Math.min(failures, 4)), signal); continue;
    }
    identity.job_id = job.job_id; remember(api, sessionId, identity); onIdentity?.(identity);
    const signature = [job.status, job.updated_at, job.content?.length, job.ready].join(':');
    if (signature !== lastSignature) { onUpdate?.(job); lastSignature = signature; }
    if (TERMINAL.has(job.status)) {
      forget(api, sessionId, identity.request_id);
      if (job.status === 'completed') return job;
      if (job.status === 'cancelled') throw abortError();
      const error = new Error(job.error?.message || 'This visual could not finish. Completed topics are kept.');
      error.visualJobFailed = true; error.visualReady = job.ready; throw error;
    }
    await wait(pollMs, signal);
  }
}
export async function cancelVisualJob(api, sessionId) {
  const identity = pendingVisualJob(api, sessionId);
  if (!identity) return null;
  const job = identity.job_id
    ? await http(api, '/chat/visual-jobs/' + encodeURIComponent(identity.job_id) + '/cancel', { method: 'POST', body: {} })
    : await http(api, '/chat/sessions/' + encodeURIComponent(sessionId) + '/visual-jobs/cancel', {
        method: 'POST', body: { request_id: identity.request_id, content: identity.content } });
  if (TERMINAL.has(job.status)) forget(api, sessionId, identity.request_id);
  return job;
}
