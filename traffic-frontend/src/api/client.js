const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

async function apiRequest(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (!options.isForm && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    try {
      const data = await resp.json();
      if (data.detail) msg = data.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  if (resp.status === 204) {
    return { status: "ok" };
  }

  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return resp.json();
  }
  return resp;
}

async function apiRequestForm(path, formData, method = "POST") {
  const token = getToken();
  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: formData,
  });

  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    try {
      const data = await resp.json();
      if (data.detail) msg = data.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  if (resp.status === 204) {
    return { status: "ok" };
  }

  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return resp.json();
  }
  return resp;
}

async function downloadByGet(path, filename) {
  const token = getToken();
  const resp = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }

  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/* -------- AUTH -------- */

export async function loginRequest(login, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ login, password }),
  });

  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

export async function loginApi(login, password) {
  return loginRequest(login, password);
}

export function logout() {
  setToken(null);
}

export function logoutApi() {
  logout();
}

export async function getMeApi() {
  return apiRequest("/users/me");
}

/* -------- USERS -------- */

export async function createUserApi(payload) {
  return apiRequest("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteUserApi(userId) {
  return apiRequest(`/users/${userId}`, {
    method: "DELETE",
  });
}

export async function resetUserPasswordApi(userId, newPassword) {
  return apiRequest(`/users/${userId}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}

/* -------- RAW GROUPS -------- */

export async function getGroups() {
  return apiRequest("/raw-groups");
}

export async function searchGroups(params = {}) {
  const qs = new URLSearchParams();

  if (params.org) qs.append("org", params.org);
  if (params.data_character) qs.append("data_character", params.data_character);
  if (params.capture_points) qs.append("capture_points", params.capture_points);

  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest(`/raw-groups/search${suffix}`);
}

export async function getGroup(groupId) {
  return apiRequest(`/raw-groups/${groupId}`);
}

export async function createGroup(payload) {
  return apiRequest("/raw-groups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function patchGroup(groupId, payload) {
  return apiRequest(`/raw-groups/${groupId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function exportGroupZip(groupId) {
  return downloadByGet(`/raw-groups/${groupId}/export`, `group_${groupId}.zip`);
}

export async function importGroupZip(zipFile) {
  const fd = new FormData();
  fd.append("file", zipFile);
  return apiRequestForm("/raw-groups/import", fd, "POST");
}

export async function uploadGroupDescription(groupId, file) {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequestForm(`/raw-groups/${groupId}/upload-description`, fd, "POST");
}

export async function uploadGroupSchema(groupId, file) {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequestForm(`/raw-groups/${groupId}/upload-schema`, fd, "POST");
}

/* -------- RAW TRACES -------- */

export async function getRawTracesByGroup(groupId) {
  return searchRawTraces({ group_id: groupId, limit: 200 });
}

export async function uploadPcapToGroup(groupId, file, point = "Single") {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequestForm(
    `/raw-traces/group/${groupId}?point=${encodeURIComponent(point)}`,
    fd,
    "POST"
  );
}

export async function uploadPcapBatchToGroup(groupId, files, point = "Single") {
  const fd = new FormData();
  for (const file of files) {
    fd.append("files", file);
  }
  return apiRequestForm(
    `/raw-traces/group/${groupId}/batch?point=${encodeURIComponent(point)}`,
    fd,
    "POST"
  );
}

export async function getRawTrace(traceId) {
  return apiRequest(`/raw-traces/${traceId}`);
}

export async function downloadRawTrace(traceId) {
  return downloadByGet(`/raw-traces/${traceId}/download`, `trace_${traceId}.pcap`);
}

export async function exportRawTraceSegment(traceId, t_from, t_to) {
  const qs = new URLSearchParams({ t_from, t_to });
  return downloadByGet(
    `/raw-traces/${traceId}/export?${qs.toString()}`,
    `trace_${traceId}_segment.pcap`
  );
}

export async function searchRawTraces(params = {}) {
  const qs = new URLSearchParams();

  if (params.group_id) qs.append("group_id", params.group_id);
  if (params.org) qs.append("org", params.org);
  if (params.data_character) qs.append("data_character", params.data_character);
  if (params.hardware_desc) qs.append("hardware_desc", params.hardware_desc);
  if (params.software_desc) qs.append("software_desc", params.software_desc);
  if (params.capture_points) qs.append("capture_points", params.capture_points);
  if (params.point) qs.append("point", params.point);
  if (params.from_ts) qs.append("from_ts", params.from_ts);
  if (params.to_ts) qs.append("to_ts", params.to_ts);
  if (params.limit) qs.append("limit", params.limit);

  return apiRequest(`/raw-traces/search?${qs.toString()}`);
}

/* -------- LABELED TRACES -------- */

export async function searchLabeledTraces(params = {}) {
  const qs = new URLSearchParams();

  if (params.kind) qs.append("kind", params.kind);
  if (params.donor_raw_trace_id) {
    qs.append("donor_raw_trace_id", params.donor_raw_trace_id);
  }
  if (params.software_desc) qs.append("software_desc", params.software_desc);
  if (params.group_id) qs.append("group_id", params.group_id);
  if (params.from_ts) qs.append("from_ts", params.from_ts);
  if (params.to_ts) qs.append("to_ts", params.to_ts);
  if (params.limit) qs.append("limit", params.limit);

  return apiRequest(`/labeled-traces/search?${qs.toString()}`);
}

export async function getLabeledTrace(labeledTraceId) {
  return apiRequest(`/labeled-traces/${labeledTraceId}`);
}

export async function downloadLabeledTrace(labeledTraceId) {
  return downloadByGet(
    `/labeled-traces/${labeledTraceId}/download`,
    `labeled_trace_${labeledTraceId}.csv`
  );
}

export async function exportLabeledTraceSegment(labeledTraceId, t_from, t_to) {
  const qs = new URLSearchParams({ t_from, t_to });
  return downloadByGet(
    `/labeled-traces/${labeledTraceId}/export?${qs.toString()}`,
    `labeled_trace_${labeledTraceId}_segment.csv`
  );
}

export async function uploadLabeledTrace(rawTraceIds, file, kind, softwareDesc = "") {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("kind", kind);
  fd.append("software_desc", softwareDesc);
  fd.append("raw_trace_ids", Array.isArray(rawTraceIds) ? rawTraceIds.join(",") : String(rawTraceIds));

  return apiRequestForm("/labeled-traces", fd, "POST");
}

export async function uploadLabeledDescription(labeledTraceId, file) {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequestForm(`/labeled-traces/${labeledTraceId}/description`, fd, "POST");
}

export async function getUserByLoginApi(login) {
  return apiRequest(`/users/by-login/${encodeURIComponent(login)}`);
}

export async function deleteUserByLoginApi(login) {
  return apiRequest(`/users/by-login/${encodeURIComponent(login)}`, {
    method: "DELETE",
  });
}

export async function resetUserPasswordByLoginApi(login, newPassword) {
  return apiRequest(`/users/by-login/${encodeURIComponent(login)}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}