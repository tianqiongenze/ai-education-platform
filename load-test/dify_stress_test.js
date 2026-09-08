// Dify 平台 5000 人并发压测 (k6)
// 模拟高职院校真实教学场景：学生上课同时使用 AI 助手
//
// Usage:
//   docker run --rm -v /tmp:/scripts -w /scripts grafana/k6 run \
//     -e BASE_URL=https://10.167.2.175:31825 dify_stress_test.js
//
// 阶梯式加压: 100 -> 500 -> 1000 -> 2000 -> 5000 VU

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import encoding from 'k6/encoding';

const BASE_URL = __ENV.BASE_URL || 'https://10.167.2.175:31825';
const EMAIL = __ENV.EMAIL || 'myuwei@126.com';
const PASSWORD = __ENV.PASSWORD || 'Difyai123456';

// 自定义指标
const chatSuccessRate = new Rate('chat_success_rate');
const chatDuration = new Trend('chat_duration_ms', true);
const platformDuration = new Trend('platform_duration_ms', true);
const streamingChunks = new Counter('streaming_chunks');

// 高职院校真实教学提问池
const TEACHING_QUESTIONS = [
  '什么是Python中的变量？',
  '请解释一下二叉树的遍历方式',
  'Java和Python哪个更适合初学者？',
  '什么是数据库的事务？',
  'TCP和UDP的区别是什么？',
  '请用C语言写一个冒泡排序',
  '什么是机器学习中的过拟合？',
  '如何理解面向对象的封装特性？',
  'SQL中的GROUP BY怎么用？',
  'HTTP状态码404是什么意思？',
  '什么是云计算的IaaS、PaaS、SaaS？',
  'JavaScript的let和var有什么区别？',
  '网络子网掩码怎么计算？',
  '什么是软件工程中的敏捷开发？',
  '请解释CSS盒模型',
  '数据结构中栈和队列的区别？',
  '什么是RESTful API？',
  'Linux常用命令有哪些？',
  'Python的列表和元组有什么区别？',
  '什么是大数据的4V特征？',
];

export const options = {
  scenarios: {
    // 场景1: 平台基础能力测试 (不依赖 LLM 推理) - 测试 HPA/ingress/DB 层
    platform: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 500 },
        { duration: '2m', target: 2000 },
        { duration: '3m', target: 5000 },
        { duration: '3m', target: 5000 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'platformTest',
    },
    // 场景2: LLM 聊天测试 (限制并发避免 LiteLLM 超时)
    llmChat: {
      executor: 'ramping-vus',
      startVUs: 0,
      startTime: '30s',
      stages: [
        { duration: '1m', target: 50 },
        { duration: '2m', target: 100 },
        { duration: '3m', target: 200 },
        { duration: '2m', target: 100 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'llmChatTest',
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.15'],
    'platform_duration_ms': ['p(95)<3000'],
    'chat_success_rate': ['rate>0.70'],
  },
  insecureSkipTLSVerify: true,
};

const vuState = {};

export function setup() {
  // 预登录获取应用信息
  const headers = { 'Host': 'console.dify-plus.local', 'Content-Type': 'application/json' };
  const passB64 = encodeBase64(PASSWORD);
  const loginResp = http.post(`${BASE_URL}/console/api/login`,
    JSON.stringify({ email: EMAIL, password: passB64, language: 'zh-Hans', remember_me: true }),
    { headers, insecureSkipTLSVerify: true });

  let appToken = null;
  let inputs = {};
  if (loginResp.status === 200) {
    const csrf = loginResp.cookies['csrf_token'] ? loginResp.cookies['csrf_token'][0].value : '';
    const authHeaders = { 'Host': 'console.dify-plus.local', 'X-CSRF-Token': csrf };
    http.get(`${BASE_URL}/console/api/apps?page=1&page_size=50`, { headers: authHeaders });

    // 获取 API key
    const keysResp = http.get(`${BASE_URL}/console/api/apps`, { headers: authHeaders });
    if (keysResp.status === 200) {
      const apps = keysResp.json('data') || [];
      const chatApp = apps.find(a => a.mode === 'chat');
      if (chatApp) {
        const keyResp = http.get(`${BASE_URL}/console/api/apps/${chatApp.id}/api-keys`, { headers: authHeaders });
        if (keyResp.status === 200) {
          const keys = keyResp.json('data') || [];
          if (keys.length > 0) {
            appToken = keys[0].token;
          }
        }
        // 获取参数
        if (appToken) {
          const paramResp = http.get(`${BASE_URL}/v1/parameters`, {
            headers: { 'Host': 'api.dify-plus.local', 'Authorization': `Bearer ${appToken}` },
            insecureSkipTLSVerify: true,
          });
          if (paramResp.status === 200) {
            const form = paramResp.json('user_input_form') || [];
            for (const item of form) {
              for (const [type, cfg] of Object.entries(item)) {
                if (cfg.required && cfg.variable) {
                  if (type === 'select') {
                    inputs[cfg.variable] = (cfg.options && cfg.options[0]) || 'True';
                  } else {
                    inputs[cfg.variable] = '老师讲课很认真，内容丰富，受益匪浅';
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  return { appToken, inputs, csrf: loginResp.cookies['csrf_token'] ? loginResp.cookies['csrf_token'][0].value : '', sessionCookie: `access_token=${loginResp.cookies['access_token'] ? loginResp.cookies['access_token'][0].value : ''}` };
}

function encodeBase64(str) {
  // k6 的 encoding.b64encode
  return encoding.b64encode(str);
}

// 平台基础能力测试：5000并发，不依赖LLM推理（测试 ingress/api/db/redis 层）
export function platformTest(data) {
  const studentId = `student-${__VU}-${__ITER}`;
  const csrfHeaders = {
    'Host': 'console.dify-plus.local',
    'X-CSRF-Token': data.csrf || '',
    'Cookie': data.sessionCookie || '',
  };

  // 1. 应用列表 (测试 DB 查询 + API 响应)
  const appsResp = http.get(`${BASE_URL}/console/api/apps?page=1&page_size=20`, {
    headers: csrfHeaders,
    tags: { name: 'apps-list' },
  });
  check(appsResp, { 'apps 200': (r) => r.status === 200 });

  // 2. 知识库列表 (测试 DB 查询)
  const dsResp = http.get(`${BASE_URL}/console/api/datasets?page=1&page_size=20`, {
    headers: csrfHeaders,
    tags: { name: 'datasets-list' },
  });
  check(dsResp, { 'datasets 200': (r) => r.status === 200 });

  // 3. 用户资料 (测试 Redis 缓存)
  const profileResp = http.get(`${BASE_URL}/console/api/account/profile`, {
    headers: csrfHeaders,
    tags: { name: 'profile' },
  });
  check(profileResp, { 'profile 200': (r) => r.status === 200 });
  platformDuration.add(profileResp.timings.waiting);

  // 4. 如果有 app token，测试对话列表 (不发起 LLM 推理)
  if (data.appToken) {
    const apiHeaders = {
      'Host': 'api.dify-plus.local',
      'Authorization': `Bearer ${data.appToken}`,
    };
    const convResp = http.get(`${BASE_URL}/v1/conversations?user=${studentId}&limit=5`, {
      headers: apiHeaders,
      tags: { name: 'conversations-list' },
    });
    check(convResp, { 'conversations 200': (r) => r.status === 200 });
    platformDuration.add(convResp.timings.waiting);
  }

  sleep(Math.random() * 2 + 0.5);
}

// LLM 聊天测试：限制并发到200，测试 LiteLLM 网关推理能力
export function llmChatTest(data) {
  if (!data.appToken) {
    sleep(5);
    return;
  }

  const studentId = `llm-student-${__VU}`;
  const query = TEACHING_QUESTIONS[Math.floor(Math.random() * TEACHING_QUESTIONS.length)];
  const headers = {
    'Host': 'api.dify-plus.local',
    'Authorization': `Bearer ${data.appToken}`,
    'Content-Type': 'application/json',
  };

  const payload = {
    inputs: data.inputs,
    query: query,
    response_mode: 'blocking',
    user: studentId,
  };

  const startTime = new Date().getTime();
  const resp = http.post(`${BASE_URL}/v1/chat-messages`, JSON.stringify(payload), {
    headers,
    tags: { name: 'chat-blocking' },
    timeout: '300s',
  });
  const duration = new Date().getTime() - startTime;

  const success = check(resp, {
    'chat 200': (r) => r.status === 200,
  });

  chatSuccessRate.add(success);
  chatDuration.add(duration);

  sleep(Math.random() * 5 + 3);
}

export default function (data) {
  // default 不执行（由 platformTest 和 llmChatTest 分场景执行）
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`/tmp/dify_stress_summary_${timestamp}.json`]: JSON.stringify(data.metrics, null, 2),
    stdout: textSummary(data),
  };
}

function textSummary(data) {
  const m = data.metrics;
  let out = '\n' + '='.repeat(70) + '\n';
  out += 'Dify 5000人并发压测结果\n' + '='.repeat(70) + '\n';

  if (m.http_req_duration) {
    out += `\nHTTP 响应时间:\n`;
    out += `  P50: ${m.http_req_duration.values['p(50)']?.toFixed(0) || 'N/A'} ms\n`;
    out += `  P90: ${m.http_req_duration.values['p(90)']?.toFixed(0) || 'N/A'} ms\n`;
    out += `  P95: ${m.http_req_duration.values['p(95)']?.toFixed(0) || 'N/A'} ms\n`;
  }
  if (m.http_reqs) {
    out += `\n总请求数: ${m.http_reqs.values.count}\n`;
    out += `吞吐量: ${(m.http_reqs.values.rate || 0).toFixed(1)} req/s\n`;
  }
  if (m.http_req_failed) {
    out += `失败率: ${((m.http_req_failed.values.rate || 0) * 100).toFixed(2)}%\n`;
  }
  if (m.chat_success_rate) {
    out += `聊天成功率: ${((m.chat_success_rate.values.rate || 0) * 100).toFixed(2)}%\n`;
  }
  if (m.vus_max) {
    out += `最大并发用户: ${m.vus_max.values.value}\n`;
  }
  out += '\n' + '='.repeat(70) + '\n';
  return out;
}
