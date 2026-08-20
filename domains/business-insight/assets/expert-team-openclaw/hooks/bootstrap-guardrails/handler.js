const fs = require("node:fs");

/**
 * agent:bootstrap —— 把共用护栏追加进引导上下文。
 * 注意：hooks 是副作用，不能阻断动作；本 hook 只做注入。
 */
const handler = async (event) => {
  const path = process.env.GUARDRAILS_PATH;
  if (!path) return;

  let text;
  try {
    text = fs.readFileSync(path.replace(/^~/, process.env.HOME || "~"), "utf8");
  } catch (err) {
    // 读不到就静默跳过：工作区的 SOUL.md 里已经内联了一份护栏，这里只是保险
    return;
  }

  event.messages.push(
    "【业务洞察专家团 · 共用护栏（bootstrap 注入）】\n" + text
  );
};

module.exports = handler;
module.exports.default = handler;
