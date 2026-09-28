async function req(method, path, body, json = false) {
  const options = { method }
  if (body) options.body = body
  if (json) options.headers = { 'Content-Type': 'application/json' }

  const res = await fetch(`/api${path}`, options)
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      if (data.detail) message = data.detail
    } catch (_) {}
    const err = new Error(message)
    err.status = res.status
    throw err
  }
  return res.json()
}

export const api = {
  status: () => req('GET', '/status'),
  datasets: () => req('GET', '/datasets'),
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return req('POST', '/datasets', formData)
  },
  remove: (id) => req('DELETE', `/datasets/${id}`),
  columns: (id) => req('GET', `/datasets/${id}/columns`),
  mapping: (id, mapping) => req('POST', `/datasets/${id}/mapping`, JSON.stringify({ mapping }), true),
  xSearch: (query, max_posts) => req('POST', '/connectors/x/search', JSON.stringify({ query, max_posts }), true),
  analyze: (id) => req('POST', `/datasets/${id}/analyze`),
  campaigns: (id) => req('GET', `/datasets/${id}/campaigns`),
  graph: (id) => req('GET', `/datasets/${id}/graph`),
  timeline: (id) => req('GET', `/datasets/${id}/timeline`),
  stats: (id) => req('GET', `/datasets/${id}/stats`),
  thread: (id, postId) => req('GET', `/datasets/${id}/posts/${encodeURIComponent(postId)}/thread`),
  posts: (id, params) => req('GET', `/datasets/${id}/posts?${new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null))}`),
  campaign: (id, cid) => req('GET', `/datasets/${id}/campaigns/${cid}`),
  verdict: (id, cid) => req('GET', `/datasets/${id}/campaigns/${cid}/verdict`),
  classify: (id, cid) => req('POST', `/datasets/${id}/campaigns/${cid}/classify`),
  briefUrl: (id) => `/api/datasets/${id}/brief`,
}
