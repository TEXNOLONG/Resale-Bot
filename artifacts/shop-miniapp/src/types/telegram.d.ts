interface TelegramWebApp {
  ready(): void;
  expand(): void;
  close(): void;
  themeParams: Record<string, string>;
  colorScheme: 'light' | 'dark';
}

interface Window {
  Telegram?: {
    WebApp?: TelegramWebApp;
  };
}
