#!/usr/bin/env node

import { execSync, spawnSync } from "child_process";
import { existsSync } from "fs";
import { join } from "path";

const BOLD = "\x1b[1m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RED = "\x1b[31m";
const CYAN = "\x1b[36m";
const NC = "\x1b[0m";

function findPython() {
  // Try candidates in order of preference
  const candidates = [
    "python3.13", "python3.12", "python3.11", "python3",
    // Homebrew paths (macOS)
    "/opt/homebrew/bin/python3.13", "/opt/homebrew/bin/python3.12", "/opt/homebrew/bin/python3.11",
    "/usr/local/bin/python3.13", "/usr/local/bin/python3.12", "/usr/local/bin/python3.11",
    // Windows
    "py -3.13", "py -3.12", "py -3.11", "python",
  ];

  for (const cmd of candidates) {
    try {
      const ver = execSync(`${cmd} -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}')"`, {
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 5000,
      }).toString().trim();
      const [major, minor] = ver.split(".").map(Number);
      if (major >= 3 && minor >= 11) {
        return { cmd, version: ver };
      }
    } catch {}
  }
  return null;
}

function main() {
  const args = process.argv.slice(2);

  // Find Python
  const python = findPython();
  if (!python) {
    console.error(`${RED}${BOLD}Error:${NC} Python 3.11+ is required but not found.`);
    console.error(`Install it via: ${CYAN}brew install python@3.11${NC} or ${CYAN}https://python.org${NC}`);
    process.exit(1);
  }

  // Check if lifeclaw Python package is installed
  try {
    execSync(`${python.cmd} -c "import lifeclaw"`, { stdio: "pipe" });
  } catch {
    // Not installed — install it
    console.log(`${CYAN}Installing LifeClaw Python package...${NC}`);
    try {
      execSync(`${python.cmd} -m pip install lifeclaw --quiet`, { stdio: "inherit" });
    } catch {
      // Try from git if not on PyPI yet
      console.log(`${YELLOW}Not on PyPI yet, installing from GitHub...${NC}`);
      execSync(`${python.cmd} -m pip install git+https://github.com/slashdoodleart/LifeClaw.git --quiet`, {
        stdio: "inherit",
      });
    }
  }

  // Run lifeclaw
  const result = spawnSync(python.cmd, ["-m", "lifeclaw", ...args], {
    stdio: "inherit",
    env: process.env,
  });

  process.exit(result.status ?? 1);
}

main();
