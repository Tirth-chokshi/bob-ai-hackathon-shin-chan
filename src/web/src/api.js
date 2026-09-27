async function req(method, path, body) {
  const options = { method };
  if (body) options.body = body;

  const res = await fetch(`/api${path}`, options);
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  status: () => req("GET", "/status"),
  datasets: () => req("GET", "/datasets"),
  upload: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return req("POST", "/datasets", formData);
  },
  remove: (id) => req("DELETE", `/datasets/${id}`),
  analyze: (id) => req("POST", `/datasets/${id}/analyze`),
  campaigns: (id) => req("GET", `/datasets/${id}/campaigns`),
  graph: (id) => req("GET", `/datasets/${id}/graph`),
  timeline: (id) => req("GET", `/datasets/${id}/timeline`),
  campaign: (id, cid) => req("GET", `/datasets/${id}/campaigns/${cid}`),
  verdict: (id, cid) => req("GET", `/datasets/${id}/campaigns/${cid}/verdict`),
  classify: (id, cid) =>
    req("POST", `/datasets/${id}/campaigns/${cid}/classify`),
  briefUrl: (id) => `/api/datasets/${id}/brief`,
};
