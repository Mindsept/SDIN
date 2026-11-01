import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const markdown = readFileSync(process.argv[2], 'utf8');
const blocks = [...markdown.matchAll(/^```ts\r?\n([\s\S]*?)^```/gm)];
assert.equal(blocks.length, 2, 'Approval reference must contain exactly Workflow and Client TS blocks');
mkdirSync('generated', { recursive: true });
for (const [index, name] of ['workflows', 'client'].entries()) {
  writeFileSync(`generated/${name}.ts`, blocks[index][1]);
}
console.log('Extracted the two unmodified TypeScript blocks from the approval guide.');
