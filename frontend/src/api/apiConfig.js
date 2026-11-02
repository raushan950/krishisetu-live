export const PRODUCTION_API_FALLBACK = 'https://krishisetu-api-70rj.onrender.com/api/v1';
export const DEVELOPMENT_API_FALLBACK = 'http://127.0.0.1:8000/api/v1';

const LOCAL_HOST_PATTERN = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?/i;

export function resolveApiBaseUrl({
  viteApiUrl = '',
  isProd = false,
  productionFallback = PRODUCTION_API_FALLBACK,
  developmentFallback = DEVELOPMENT_API_FALLBACK,
} = {}) {
  let url = String(viteApiUrl || '').trim();

  if (!url) {
    url = isProd ? productionFallback : developmentFallback;
  }

  url = url.replace(/\/+$/, '');

  if (isProd && LOCAL_HOST_PATTERN.test(url)) {
    console.error(
      'KrishiSetu: production build is pointing at a localhost API URL. Using the Render API instead. Set VITE_API_URL in Vercel and rebuild the frontend.'
    );
    url = productionFallback.replace(/\/+$/, '');
  }

  // Collapse accidental duplicate /api/v1 segments.
  url = url.replace(/(\/api\/v1)+$/i, '/api/v1');

  if (!/\/api\/v1$/i.test(url)) {
    console.warn(
      'KrishiSetu: API base URL should end with /api/v1. Current value:',
      url
    );
  }

  return url;
}
