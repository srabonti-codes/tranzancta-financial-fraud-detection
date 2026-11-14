function getApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL?.trim();
  if (configuredUrl) return configuredUrl.replace(/\/+$/, '');
  if (import.meta.env.DEV) return '';
  throw new Error('VITE_API_URL is not configured for this deployment.');
}

async function request(path, options) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, options);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg || 'Invalid input').join('; ')
      : detail || (typeof payload === 'string' ? payload : 'Request failed');
    throw new Error(message);
  }
  return payload;
}

export function apiGet(path) {
  return request(path);
}

export function apiPost(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
