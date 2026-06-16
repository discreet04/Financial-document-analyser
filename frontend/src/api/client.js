const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const AUTH_STORAGE_KEYS = ["financial_rag_token", "financial_rag_user"];

function clearStoredAuth() {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
  window.dispatchEvent(new Event("financial-rag-auth-expired"));
}

async function request(path, options = {}) {
  const token = localStorage.getItem("financial_rag_token");
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the backend at ${API_BASE_URL}. Start the API server and check CORS settings.`);
    }
    throw error;
  }

  if (!response.ok) {
    let message = "Request failed";
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      message = response.statusText || message;
    }
    if (response.status === 401) {
      clearStoredAuth();
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  health: () => request("/health"),
  register: (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  dashboard: () => request("/dashboard"),
  documents: () => request("/documents"),
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/documents/upload", { method: "POST", body: formData });
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  askQuestion: (payload) => request("/chat/query", { method: "POST", body: JSON.stringify(payload) }),
  chatHistory: () => request("/chat/history"),
  summarizeDocument: (id) => request(`/documents/${id}/summary`, { method: "POST" }),
};
