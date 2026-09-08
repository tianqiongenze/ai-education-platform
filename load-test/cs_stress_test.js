// Code-Server 2000人压测 (k6)
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    code_server_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },
        { duration: '2m', target: 500 },
        { duration: '2m', target: 1000 },
        { duration: '2m', target: 2000 },
        { duration: '3m', target: 2000 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.15'],
    'http_req_duration': ['p(95)<10000'],
  },
  insecureSkipTLSVerify: true,
};

export default function () {
  // 1. Login page
  let r = http.get('https://10.167.2.175:31825/cs/', { headers: { 'Host': '10.167.2.175' } });
  check(r, { 'login page': (res) => res.status === 200 || res.status === 302 });

  // 2. Health check
  r = http.get('https://10.167.2.175:31825/cs/healthz', { headers: { 'Host': '10.167.2.175' } });
  check(r, { 'health': (res) => res.status === 200 || res.status === 302 || res.status === 401 });

  // 3. Static assets
  r = http.get('https://10.167.2.175:31825/cs/_static/src/browser/manifest.json', { headers: { 'Host': '10.167.2.175' } });
  check(r, { 'static': (res) => res.status === 200 || res.status === 302 || res.status === 404 });

  // Simulate user activity
  sleep(Math.random() * 5 + 2);
}

export function handleSummary(data) {
  return {
    'D:/dify-install/load-test/cs_stress_report.json': JSON.stringify(data.metrics, null, 2),
    stdout: `\n=== Code-Server Stress Test Results ===\n` +
      `Total Requests: ${data.metrics.http_reqs.values.count}\n` +
      `Throughput: ${data.metrics.http_reqs.values.rate.toFixed(1)} req/s\n` +
      `Failed: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%\n` +
      `P50: ${data.metrics.http_req_duration.values['p(50)'].toFixed(0)}ms\n` +
      `P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(0)}ms\n` +
      `Max VUs: ${data.metrics.vus_max.values.value}\n` +
      `========================================\n`,
  };
}
