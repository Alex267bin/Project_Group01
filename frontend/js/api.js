const API_BASE_URL = "http://127.0.0.1:8000";

async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {})
  };

  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal
    });

    if (response.status === 401) {
      logout();
      throw new Error("Your session has expired. Please sign in again.");
    }

    if (!response.ok) {
      const text = await response.text();
      let message = text || `Request failed with status ${response.status}`;
      try {
        const parsed = JSON.parse(text);
        if (parsed?.detail) message = parsed.detail;
      } catch (_) {}
      throw new Error(message);
    }

    if (response.status === 204) return null;

    const contentType = response.headers.get("content-type") || "";
    return contentType.includes("application/json")
      ? await response.json()
      : response;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The server did not respond within 10 seconds.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function login(username, password) {
  const result = await apiRequest("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });

  if (!result?.access_token) {
    throw new Error("Authentication succeeded but no access token was returned.");
  }

  localStorage.setItem("access_token", result.access_token);
  localStorage.setItem("token_type", result.token_type || "bearer");
  return result;
}

function decodeTokenPayload(token = localStorage.getItem("access_token")) {
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    const normalized = part.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch (_) {
    return null;
  }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");
  localStorage.removeItem("selected_role");
}

async function getAttendanceHistory() {
  return apiRequest("/api/v1/attendance/me");
}

async function scanAttendance(payload) {
  return apiRequest("/api/v1/attendance/scan", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

async function activateSession(payload) {
  return apiRequest("/api/v1/sessions/activate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

async function refreshSessionQr(sessionId) {
  return apiRequest(`/api/v1/sessions/${encodeURIComponent(sessionId)}/qr`);
}

async function getSessionAttendance(sessionId) {
  return apiRequest(`/api/v1/attendance/sessions/${encodeURIComponent(sessionId)}`);
}

async function updateAttendance(recordId, status) {
  return apiRequest(`/api/v1/attendance/records/${encodeURIComponent(recordId)}`, {
    method: "PUT",
    body: JSON.stringify({ status })
  });
}

async function getUsers() {
  return apiRequest("/api/v1/users");
}

async function createUser(payload) {
  return apiRequest("/api/v1/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

async function updateUser(userId, payload) {
  return apiRequest(`/api/v1/users/${encodeURIComponent(userId)}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

async function deleteUser(userId) {
  return apiRequest(`/api/v1/users/${encodeURIComponent(userId)}`, {
    method: "DELETE"
  });
}

async function getCourses() {
  return apiRequest("/api/v1/courses");
}
