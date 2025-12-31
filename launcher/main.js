const { app, BrowserWindow, BrowserView } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let browserViews = []; // Array of 9 BrowserViews
let pythonProcess;
let dashboardReady = false;
const NUM_AGENTS = 9;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1800,
        height: 1200,
        frame: true,
        backgroundColor: '#000000',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        title: "Browser Agent - 9 Instance Grid"
    });

    // Create 9 BrowserViews for the grid
    for (let i = 0; i < NUM_AGENTS; i++) {
        const view = new BrowserView({
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
            }
        });

        mainWindow.addBrowserView(view);
        view.setBounds({ x: 0, y: 0, width: 0, height: 0 }); // Initially hidden
        view.webContents.loadURL('about:blank');

        browserViews.push(view);
    }

    // Setup listener BEFORE loading file
    mainWindow.webContents.once('did-finish-load', () => {
        if (mainWindow) mainWindow.webContents.send('log-message', "🚀 Initializing 9-Agent System...");
        startPythonServer();
    });

    // Load the loading screen
    mainWindow.loadFile('index.html');

    // Handle window resize to update grid bounds
    mainWindow.on('resize', updateGridLayout);

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

function updateGridLayout() {
    if (!mainWindow || !dashboardReady) return;

    const bounds = mainWindow.getBounds();
    const dashboardWidth = 400; // Left panel for dashboard
    const gridStartX = dashboardWidth;
    const gridWidth = bounds.width - dashboardWidth;
    const gridHeight = bounds.height;

    // 3x3 grid
    const cellWidth = Math.floor(gridWidth / 3);
    const cellHeight = Math.floor(gridHeight / 3);

    for (let i = 0; i < NUM_AGENTS; i++) {
        const row = Math.floor(i / 3);
        const col = i % 3;

        browserViews[i].setBounds({
            x: gridStartX + (col * cellWidth),
            y: row * cellHeight,
            width: cellWidth,
            height: cellHeight
        });
    }
}

function showGridView() {
    if (!mainWindow) return;

    dashboardReady = true;

    // Load CDP endpoints for each agent
    // For now, just show about:blank in each cell
    for (let i = 0; i < NUM_AGENTS; i++) {
        browserViews[i].webContents.loadURL('about:blank');
    }

    updateGridLayout();
}

function killPortProcess(port) {
    return new Promise((resolve) => {
        const { exec } = require('child_process');

        const killCmd = process.platform === 'win32'
            ? `netstat -ano | findstr :${port} | findstr LISTENING`
            : `lsof -ti:${port}`;

        exec(killCmd, (error, stdout) => {
            if (error || !stdout) {
                resolve();
                return;
            }

            const finalKillCmd = process.platform === 'win32'
                ? `taskkill /F /PID ${stdout.trim().split(/\s+/).pop()}`
                : `kill -9 ${stdout.trim()}`;

            exec(finalKillCmd, () => {
                console.log(`Killed process on port ${port}`);
                if (mainWindow) {
                    mainWindow.webContents.send('log-message', `🧹 Cleared port ${port}`);
                }
                resolve();
            });
        });
    });
}

async function startPythonServer() {
    if (pythonProcess) {
        console.log("Python server already running.");
        if (mainWindow) mainWindow.webContents.send('log-message', "⚠️ Server already running");
        return;
    }

    await killPortProcess(8000);

    const HARDCODED_ROOT = '/Users/reneturcios/browser';
    let rootDir = HARDCODED_ROOT;

    let venvPath = '';
    if (process.platform === 'win32') {
        venvPath = path.join(HARDCODED_ROOT, 'venv', 'Scripts', 'python.exe');
    } else {
        venvPath = path.join(HARDCODED_ROOT, 'venv', 'bin', 'python3');
    }

    const serverPath = "browser_agent.server.main:app";

    console.log(`Starting Python Server from: ${rootDir} using ${venvPath}`);

    if (mainWindow) {
        mainWindow.webContents.send('log-message', `📂 Root: ${rootDir}`);
        mainWindow.webContents.send('log-message', `🐍 Python: ${venvPath}`);
        mainWindow.webContents.send('log-message', `⏳ Starting 9-agent server...`);
    }

    try {
        pythonProcess = spawn(venvPath, ['-m', 'uvicorn', serverPath, '--host', '0.0.0.0', '--port', '8000'], {
            cwd: rootDir
        });

        pythonProcess.on('error', (err) => {
            console.error('Failed to start python process.', err);
            if (mainWindow) mainWindow.webContents.send('log-message', `❌ SPAWN ERROR: ${err.message}`);
        });

        pythonProcess.stdout.on('data', (data) => {
            console.log(`[Python]: ${data}`);
            if (mainWindow) mainWindow.webContents.send('log-message', data.toString().trim());
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`[Python]: ${data}`);
            if (mainWindow) mainWindow.webContents.send('log-message', `⚠️ ${data.toString().trim()}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            if (mainWindow) mainWindow.webContents.send('log-message', `🛑 Server stopped (code ${code})`);
            pythonProcess = null;
        });
    } catch (e) {
        if (mainWindow) mainWindow.webContents.send('log-message', `❌ CRITICAL: ${e.message}`);
    }
}

function checkServer() {
    http.get('http://localhost:8000', (res) => {
        if (res.statusCode === 200) {
            console.log("Server ready! Loading dashboard...");
            if (mainWindow) {
                // Load dashboard in main window (left panel)
                mainWindow.loadURL('http://localhost:8000');
                // Show the 3x3 grid
                showGridView();
            }
        }
    }).on('error', (e) => {
        setTimeout(checkServer, 1000);
    });
}

app.whenReady().then(() => {
    createWindow();
    checkServer();

    app.on('activate', function () {
        if (mainWindow === null) createWindow();
    });
});

app.on('window-all-closed', function () {
    app.quit();
});

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
