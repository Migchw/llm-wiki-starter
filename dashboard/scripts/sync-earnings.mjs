// Runs the vault's /earnings-scorecard script (Python + yfinance) to refresh data/earnings-data.json.
// yfinance is Python-only, so this wrapper tries the usual interpreters and never fails the build:
// if none works it keeps the previous file, or writes an empty one so the dashboard still compiles.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const vaultRoot = process.env.WIKI_VAULT_PATH || path.resolve(projectRoot, '..');
const script = path.join(vaultRoot, '.agents', 'skills', 'earnings-scorecard', 'scripts', 'earnings_scorecard.py');
const outFile = path.join(projectRoot, 'data', 'earnings-data.json');
const passThrough = process.argv.slice(2);

async function ensureFile() {
  if (existsSync(outFile)) return;
  await mkdir(path.dirname(outFile), { recursive: true });
  await writeFile(outFile, `${JSON.stringify({ provider: 'not synced', fetchedAt: '', scorecards: {} }, null, 2)}\n`, 'utf8');
}

if (!existsSync(script)) {
  console.warn(`earnings: script not found at ${script}; skipped`);
  await ensureFile();
  process.exit(0);
}

for (const cmd of ['py', 'python3', 'python']) {
  const result = spawnSync(cmd, [script, '--vault', vaultRoot, ...passThrough], { stdio: 'inherit', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  if (result.error?.code === 'ENOENT') continue;
  if (result.status === 0) process.exit(0);
  console.warn(`earnings: ${cmd} exited with ${result.status}; trying the next interpreter`);
}

console.warn('earnings: no Python with yfinance succeeded (py -m pip install yfinance); keeping previous data');
await ensureFile();
