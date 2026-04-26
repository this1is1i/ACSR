module.exports = {
  testDir: './tests',
  testMatch: 'paper-detail.spec.js',
  timeout: 30000,
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    port: 4173,
    reuseExistingServer: false,
  },
  use: {
    headless: true,
    baseURL: 'http://127.0.0.1:4173',
  },
};
