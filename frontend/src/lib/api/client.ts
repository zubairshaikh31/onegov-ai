import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/authStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = useAuthStore.getState().accessToken;
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

let _refreshing = false;
let _queue: Array<{ resolve: (t: string) => void; reject: (e: unknown) => void }> = [];

function processQueue(err: unknown, token: string | null) {
  _queue.forEach(({ resolve, reject }) => (err ? reject(err) : resolve(token!)));
  _queue = [];
}

apiClient.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const req = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (!req || error.response?.status !== 401 || req._retry || req.url?.includes("/auth/")) {
      return Promise.reject(error);
    }

    const { refreshToken, clearAuth, setTokens } = useAuthStore.getState();

    if (_refreshing) {
      return new Promise<string>((resolve, reject) => {
        _queue.push({ resolve, reject });
      })
        .then((token) => {
          req.headers.Authorization = `Bearer ${token}`;
          return apiClient(req);
        })
        .catch((err) => Promise.reject(err));
    }

    req._retry = true;
    _refreshing = true;

    try {
      // The refresh token lives in the HttpOnly cookie (XSS-safe); the in-memory
      // refreshToken is only a cache. Sending an empty body relies on the cookie.
      const { data } = await axios.post(
        `${API_BASE}/auth/refresh`,
        refreshToken ? { refresh_token: refreshToken } : {},
        { withCredentials: true }
      );
      const { access_token, refresh_token: new_refresh_token } = data.data;
      setTokens(access_token, new_refresh_token ?? refreshToken ?? "");
      processQueue(null, access_token);
      req.headers.Authorization = `Bearer ${access_token}`;
      return apiClient(req);
    } catch (e) {
      processQueue(e, null);
      clearAuth();
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(e);
    } finally {
      _refreshing = false;
    }
  },
);

export default apiClient;

