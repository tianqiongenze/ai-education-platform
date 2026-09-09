// k6 压力测试脚本 - 在线编程平台全链路
// 用法: k6 run k6_stress_test.js
// 输出: JSON metrics + 自定义报告

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ── 配置 ──
const LMS = 'https://openedx.10.167.2.175.nip.io:31825';
const STUDIO = 'https://studio.openedx.10.167.2.175.nip.io:31825';
const HUB = 'https://10.167.2.175:31825';
const PRAIRIE = 'http://10.167.2.175:30093';
const COURSES = ['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','P1','P2','P3','P4','P5','P6'];

// ── 自定义指标 ──
const lmsSuccessRate = new Rate('lms_success_rate');
const studioSuccessRate = new Rate('studio_success_rate');
const hubSuccessRate = new Rate('hub_success_rate');
const prairieSuccessRate = new Rate('prairie_success_rate');
const oauthRedirectTrend = new Trend('oauth_redirect_time');
const errorCounter = new Counter('total_errors');

// ── 压力测试配置 ──
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // 预热: 0→20 VUs
    { duration: '1m', target: 50 },    // 正常负载: 20→50 VUs
    { duration: '30s', target: 100 },   // 峰值: 50→100 VUs
    { duration: '1m', target: 100 },    // 持续峰值: 100 VUs
    { duration: '30s', target: 0 },     // 降温: 100→0 VUs
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95%请求<5s
    http_req_failed: ['rate<0.1'],       // 失败率<10%
    lms_success_rate: ['rate>0.9'],
    studio_success_rate: ['rate>0.9'],
    hub_success_rate: ['rate>0.9'],
    prairie_success_rate: ['rate>0.9'],
  },
  insecureSkipTLSVerify: true,
};

const params = {
  insecureSkipTLSVerify: true,
  redirects: 0, // Don't follow redirects - count them as success
  timeout: '15s',
};

export default function () {
  const course = COURSES[Math.floor(Math.random() * COURSES.length)];

  // ── LMS Tests ──
  group('LMS', function () {
    // LMS homepage
    let r = http.get(LMS + '/', params);
    const ok1 = check(r, {
      'LMS首页 200/302': (r) => r.status === 200 || r.status === 302 || r.status === 301,
    });
    lmsSuccessRate.add(ok1);
    if (!ok1) errorCounter.add(1);

    // LMS course page
    r = http.get(LMS + `/courses/course-v1:AIEDU+${course}+2026/courseware/`, params);
    const ok2 = check(r, {
      'LMS课程页 200/302': (r) => r.status === 200 || r.status === 302 || r.status === 301,
    });
    lmsSuccessRate.add(ok2);
    if (!ok2) errorCounter.add(1);

    // LMS OAuth authorize
    const t0 = Date.now();
    r = http.get(LMS + '/oauth2/authorize/?response_type=code&client_id=REDACTED_OAUTH_CLIENT_ID&redirect_uri=https://10.167.2.175:31825/ide/hub/oauth_callback&scope=user_id', params);
    oauthRedirectTrend.add(Date.now() - t0);
    const ok3 = check(r, {
      'OAuth授权 200/302': (r) => r.status === 200 || r.status === 302 || r.status === 301,
    });
    lmsSuccessRate.add(ok3);
    if (!ok3) errorCounter.add(1);
  });

  // ── Studio Tests ──
  group('Studio', function () {
    // Studio homepage
    let r = http.get(STUDIO + '/', params);
    const ok1 = check(r, {
      'Studio首页 200/302': (r) => r.status === 200 || r.status === 302,
    });
    studioSuccessRate.add(ok1);
    if (!ok1) errorCounter.add(1);

    // Studio course settings (404 fix verification under load)
    r = http.get(STUDIO + `/settings/details/course-v1:AIEDU+${course}+2026`, params);
    const ok2 = check(r, {
      'Studio课程设置 200/302': (r) => r.status === 200 || r.status === 302 || r.status === 301,
    });
    studioSuccessRate.add(ok2);
    if (!ok2) errorCounter.add(1);

    // Studio course-authoring MFE
    r = http.get(STUDIO + `/course-authoring/course-v1:AIEDU+${course}+2026`, params);
    const ok3 = check(r, {
      'Studio课程创作 200/302': (r) => r.status === 200 || r.status === 302,
    });
    studioSuccessRate.add(ok3);
    if (!ok3) errorCounter.add(1);
  });

  // ── JupyterHub Tests ──
  group('JupyterHub', function () {
    // Hub login page
    let r = http.get(HUB + '/ide/hub/login', params);
    const ok1 = check(r, {
      'Hub登录 200/302': (r) => r.status === 200 || r.status === 302,
    });
    hubSuccessRate.add(ok1);
    if (!ok1) errorCounter.add(1);

    // Hub OAuth redirect
    r = http.get(HUB + '/ide/hub/oauth_login', params);
    const ok2 = check(r, {
      'Hub OAuth 200/302/301': (r) => r.status === 200 || r.status === 302 || r.status === 301,
    });
    hubSuccessRate.add(ok2);
    if (!ok2) errorCounter.add(1);

    // Hub healthcheck
    r = http.get(HUB + '/ide/hub/healthcheck', params);
    const ok3 = check(r, {
      'Hub健康 200': (r) => r.status === 200,
    });
    hubSuccessRate.add(ok3);
    if (!ok3) errorCounter.add(1);
  });

  // ── PrairieLearn Tests ──
  group('PrairieLearn', function () {
    let r = http.get(PRAIRIE + '/', params);
    const ok1 = check(r, {
      'PL首页 200/302': (r) => r.status === 200 || r.status === 302,
    });
    prairieSuccessRate.add(ok1);
    if (!ok1) errorCounter.add(1);

    r = http.get(PRAIRIE + '/health', params);
    const ok2 = check(r, {
      'PL健康 200': (r) => r.status === 200,
    });
    prairieSuccessRate.add(ok2);
    if (!ok2) errorCounter.add(1);
  });

  sleep(Math.random() * 2 + 1); // 1-3s think time
}

// ── 清理函数 ──
export function teardown() {
  console.log('k6 stress test completed - test data cleanup is handled by the Locust/CRDB cleanup script');
}
