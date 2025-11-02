const { app, BrowserWindow, Menu, Tray, dialog } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let flaskProcess;
let tray;
const FLASK_PORT = 5000;
const isDev = process.argv.includes('--dev');

// Configure auto-updater
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

// Logging
autoUpdater.logger = require('electron-log');
autoUpdater.logger.transports.file.level = 'info';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    icon: path.join(__dirname, '../assets/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false,
    backgroundColor: '#1a1a2e'
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Load the Flask app
  const loadApp = () => {
    mainWindow.loadURL(`http://localhost:${FLASK_PORT}`)
      .catch(() => {
        // Retry after 500ms if Flask isn't ready yet
        setTimeout(loadApp, 500);
      });
  };

  // Wait for Flask to start, then load
  setTimeout(loadApp, 2000);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create system tray
  createTray();
}

function createTray() {
  const iconPath = path.join(__dirname, '../assets/icon.ico');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Ultimate Network Tool');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

function startFlaskServer() {
  return new Promise((resolve, reject) => {
    let flaskPath;

    if (isDev) {
      // Development mode: use Python directly
      console.log('Starting Flask in development mode...');
      flaskPath = 'python';
      const appPath = path.join(__dirname, '../app.py');
      flaskProcess = spawn(flaskPath, [appPath], {
        cwd: path.join(__dirname, '..')
      });
    } else {
      // Production mode: use PyInstaller executable
      console.log('Starting Flask in production mode...');
      if (process.resourcesPath) {
        flaskPath = path.join(process.resourcesPath, 'app', 'app.exe');
      } else {
        flaskPath = path.join(__dirname, '../dist/app/app.exe');
      }

      flaskProcess = spawn(flaskPath, [], {
        cwd: path.dirname(flaskPath)
      });
    }

    flaskProcess.stdout.on('data', (data) => {
      console.log(`Flask: ${data}`);
      if (data.toString().includes('Running on')) {
        resolve();
      }
    });

    flaskProcess.stderr.on('data', (data) => {
      console.error(`Flask Error: ${data}`);
    });

    flaskProcess.on('close', (code) => {
      console.log(`Flask process exited with code ${code}`);
    });

    flaskProcess.on('error', (err) => {
      console.error('Failed to start Flask:', err);
      reject(err);
    });

    // Timeout after 10 seconds
    setTimeout(() => resolve(), 10000);
  });
}

function stopFlaskServer() {
  if (flaskProcess) {
    console.log('Stopping Flask server...');

    // Kill Flask process
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', flaskProcess.pid, '/f', '/t']);
    } else {
      flaskProcess.kill();
    }

    flaskProcess = null;
  }
}

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  console.log('Checking for updates...');
});

autoUpdater.on('update-available', (info) => {
  console.log('Update available:', info.version);

  dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: `A new version (${info.version}) is available. Would you like to download it now?`,
    buttons: ['Download', 'Later']
  }).then((result) => {
    if (result.response === 0) {
      autoUpdater.downloadUpdate();
    }
  });
});

autoUpdater.on('update-not-available', () => {
  console.log('No updates available');
});

autoUpdater.on('download-progress', (progressObj) => {
  let message = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`;
  console.log(message);

  if (mainWindow) {
    mainWindow.setProgressBar(progressObj.percent / 100);
  }
});

autoUpdater.on('update-downloaded', (info) => {
  console.log('Update downloaded:', info.version);

  if (mainWindow) {
    mainWindow.setProgressBar(-1); // Remove progress bar
  }

  dialog.showMessageBox({
    type: 'info',
    title: 'Update Ready',
    message: `Version ${info.version} has been downloaded. The application will restart to install the update.`,
    buttons: ['Restart Now', 'Later']
  }).then((result) => {
    if (result.response === 0) {
      autoUpdater.quitAndInstall();
    }
  });
});

autoUpdater.on('error', (err) => {
  console.error('Update error:', err);
});

// App lifecycle
app.whenReady().then(async () => {
  try {
    // Start Flask server first
    await startFlaskServer();

    // Create window
    createWindow();

    // Check for updates (only in production)
    if (!isDev) {
      setTimeout(() => {
        autoUpdater.checkForUpdates();
      }, 5000);

      // Check for updates every 4 hours
      setInterval(() => {
        autoUpdater.checkForUpdates();
      }, 4 * 60 * 60 * 1000);
    }
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', 'Failed to start the Flask server. Please ensure you have admin privileges.');
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
});

app.on('quit', () => {
  stopFlaskServer();
});

// Handle second instance
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}
