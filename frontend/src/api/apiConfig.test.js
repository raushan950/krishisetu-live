import { describe, expect, it, vi } from 'vitest';
import { resolveApiBaseUrl, PRODUCTION_API_FALLBACK, DEVELOPMENT_API_FALLBACK } from './apiConfig';

describe('resolveApiBaseUrl', () => {
  it('uses the local Django API in development when VITE_API_URL is empty', () => {
    expect(resolveApiBaseUrl({ viteApiUrl: '', isProd: false })).toBe(DEVELOPMENT_API_FALLBACK);
  });

  it('uses the Render API in production when VITE_API_URL is empty', () => {
    expect(resolveApiBaseUrl({ viteApiUrl: '', isProd: true })).toBe(PRODUCTION_API_FALLBACK);
  });

  it('strips trailing slashes and duplicate /api/v1 segments', () => {
    expect(
      resolveApiBaseUrl({
        viteApiUrl: 'https://krishisetu-api-70rj.onrender.com/api/v1/api/v1/',
        isProd: true,
      })
    ).toBe(PRODUCTION_API_FALLBACK);
  });

  it('rejects localhost API URLs in production builds', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(
      resolveApiBaseUrl({
        viteApiUrl: 'http://127.0.0.1:8000/api/v1',
        isProd: true,
      })
    ).toBe(PRODUCTION_API_FALLBACK);
    spy.mockRestore();
  });
});
