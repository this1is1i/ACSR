module.exports = {
  testDir: './tests',
  timeout: 30000,
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
  use: {
    headless: true,
    baseURL: 'http://localhost:5173',
  },
};
