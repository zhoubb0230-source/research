const fs = require("node:fs");
const path = require("node:path");

/** 把事件按行追加到 JSONL 台账。纯副作用，不影响流程。 */
const handler = async (event) => {
  const raw = process.env.LEDGER_PATH || "~/.openclaw/logs/business-insight-ledger.jsonl";
  const file = raw.replace(/^~/, process.env.HOME || "~");

  const record = {
    ts: new Date().toISOString(),
    type: event?.type ?? null,
    action: event?.action ?? null,
    sessionKey: event?.sessionKey ?? null,
    // sessionKey 形如 agent:<agentId>:subagent:<uuid>，从中还原是哪个专家
    agentId: typeof event?.sessionKey === "string" ? event.sessionKey.split(":")[1] ?? null : null,
  };

  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.appendFileSync(file, JSON.stringify(record) + "\n", "utf8");
  } catch {
    // 留痕失败不得影响主流程
  }
};

module.exports = handler;
module.exports.default = handler;
