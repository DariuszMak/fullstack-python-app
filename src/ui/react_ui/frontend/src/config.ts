declare global {
  interface Window {
    __APP_CONFIG__?: AppConfig;
  }

  var __APP_CONFIG__: AppConfig | undefined;
}

export function getApiBaseUrl(): string {
  return (
    globalThis.__APP_CONFIG__?.apiBaseUrl ??
    (import.meta.env.VITE_BACKEND_URL as string | undefined) ??
    "http://localhost:8000"
  );
}
