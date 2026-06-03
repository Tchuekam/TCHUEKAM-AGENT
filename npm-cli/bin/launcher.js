#!/usr/bin/env node

const { program } = require('commander');
const execa = require('execa');
const semver = require('semver');
const open = require('open');
const path = require('path');
const sysProcess = require('process');
const fs = require('fs');

// Resolve the python backend directory path
function resolveBackendPath() {
  const candidates = [
    path.resolve(__dirname, '../../tchuekam-agent/app'), // Local repo dev mode
    path.resolve(__dirname, '../tchuekam-agent/app'),    // Bundled relative structure
    path.resolve(__dirname, '..'),                       // Flat structure
  ];

  for (const c of candidates) {
    if (fs.existsSync(path.join(c, 'tchuekam_cli', 'main.py'))) {
      return c;
    }
  }

  throw new Error('Could not resolve TchuEkaM backend path (tchuekam_cli/main.py not found).');
}

// System prerequisite checks
async function verifyEnvironment() {
  try {
    const { stdout: pyVer } = await execa('python', ['--version']);
    const match = pyVer.match(/Python\s+([\d.]+)/);
    if (!match || semver.lt(match[1], '3.10.0')) {
      console.error(`❌ Python 3.10+ is required. Detected version: ${pyVer.trim()}`);
      sysProcess.exit(1);
    }
  } catch (err) {
    console.error('❌ Python is not installed or not exposed in system environment variables (PATH).');
    sysProcess.exit(1);
  }
}

// Start backend daemon
async function startDaemon(port) {
  let backendPath;
  try {
    backendPath = resolveBackendPath();
  } catch (err) {
    console.error(err.message);
    sysProcess.exit(1);
  }

  console.log('⚡ Initializing TchuEkaM Server...');
  console.log(`📂 Backend workspace: ${backendPath}`);

  // Spawn Python backend process
  const child = execa('python', ['-m', 'tchuekam_cli.main', 'web', '--port', port], {
    cwd: backendPath,
    stdio: 'inherit',
    env: {
      ...sysProcess.env,
      TCHUEKAM_NONINTERACTIVE: '1'
    }
  });

  child.on('close', (code) => {
    console.log(`\n🛑 TchuEkaM daemon exited with code: ${code}`);
    sysProcess.exit(code || 0);
  });

  // Open default browser on loopback port
  setTimeout(async () => {
    const url = `http://127.0.0.1:${port}`;
    console.log(`🌐 Application UI serving at: ${url}`);
    try {
      await open(url);
    } catch (e) {
      // Non-fatal if open fails (e.g. headless system)
    }
  }, 1500);
}

program
  .name('tchuekam')
  .description('Tchuekam Client CLI')
  .version('1.0.0');

program
  .command('start')
  .description('Start the local workstation daemon and UI browser interface')
  .option('-p, --port <number>', 'Port to bind', '9119')
  .action(async (options) => {
    await verifyEnvironment();
    await startDaemon(options.port);
  });

program.parse(sysProcess.argv);
