import fs from "node:fs";

const testCmd = "node --test practice/**/*.test.mjs";
const covCmd =
  "node --test --experimental-test-coverage --test-coverage-lines=50 --test-coverage-functions=50 --test-coverage-branches=40 practice/**/*.test.mjs";

const apps = process.argv.slice(2);
for (const app of apps) {
  const p = `${app}/package.json`;
  const j = JSON.parse(fs.readFileSync(p, "utf8"));
  j.scripts = j.scripts || {};
  j.scripts.test = testCmd;
  j.scripts["test:coverage"] = covCmd;
  fs.writeFileSync(p, JSON.stringify(j, null, 2) + "\n");
  console.log("updated", p);
}
