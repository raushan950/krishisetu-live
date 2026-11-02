import axios from 'axios';
import { resolveApiBaseUrl } from './apiConfig';

export const API_BASE_URL = resolveApiBaseUrl({
  viteApiUrl: import.meta.env.VITE_API_URL,
  isProd: import.meta.env.PROD,
});

const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const clearSession = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_info');
  window.dispatchEvent(new Event('auth:session-expired'));
};

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login/') &&
      !originalRequest.url?.includes('/auth/register/') &&
      !originalRequest.url?.includes('/auth/refresh/')
    ) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        clearSession();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return axiosClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;

      try {
        const res = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        if (res.status === 200 && res.data.access) {
          const newAccess = res.data.access;
          localStorage.setItem('access_token', newAccess);

          if (res.data.refresh) {
            localStorage.setItem('refresh_token', res.data.refresh);
          }

          window.dispatchEvent(new CustomEvent('auth:token-refreshed', {
            detail: { access: newAccess },
          }));

          processQueue(null, newAccess);
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return axiosClient(originalRequest);
        }

        clearSession();
        processQueue(error, null);
        return Promise.reject(error);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        clearSession();
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default axiosClient;
