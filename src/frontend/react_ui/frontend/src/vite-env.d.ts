interface AppConfig {
  apiBaseUrl: string;
}

interface Window {
  __APP_CONFIG__?: AppConfig;
}
