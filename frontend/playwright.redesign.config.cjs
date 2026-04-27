module.exports = {
  testDir: './tests',
  testMatch: [
    'ui-shell.spec.js',
    'home-hub.spec.js',
    'search-detail-redesign.spec.js',
    'path-surfaces.spec.js',
    'collaboration-workspace.spec.js',
    'admin-cockpit.spec.js',
  ],
  timeout: 30000,
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4174',
    port: 4174,
    reuseExistingServer: false,
  },
  use: {
    headless: true,
    baseURL: 'http://127.0.0.1:4174',
  },
}
