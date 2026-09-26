async function req(method, path, body) {
  const options = { method }
  if (body) {
    if (body instanceof FormData) {
      options.body = body
    } else {
      options.headers = { 'Content-Type': 'application/json' }
      options.body = JSON.stringify(body)
    }
  }

  const res = await fetch(`/api${path}`, options)
  if (!res.ok) {
    let errMessage = `${res.status} ${res.statusText}`
    try {
      const errData = await res.json()
      if (errData.detail) errMessage = errData.detail
    } catch (_) {}
    throw new Error(errMessage)
  }
  return res.json()
}

export const api = {
  status: () => req('GET', '/status'),
  datasets: () => req('GET', '/datasets/demo'),
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return req('POST', '/datasets', formData)
  },
  analyze: (id) => req('POST', `/datasets/${id}/analyze`),
  graph: (id) => req('GET', `/datasets/${id}/graph`),
  timeline: (id) => req('GET', `/datasets/${id}/timeline`),
  campaign: (id, cid) => req('GET', `/datasets/${id}/campaigns/${cid}`),
  classify: (id, cid) => req('POST', `/datasets/${id}/campaigns/${cid}/classify`),
  briefUrl: (id) => `/api/datasets/${id}/brief`,
}
