const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const isDev = !app.isPackaged

let backendProcess = null

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true
    },
    show: false
  })

  win.once('ready-to-show', () => {
    win.show()
  })

  if (isDev) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools()
  } else {
    // In production, frontend dist is relative to app path
    win.loadFile(path.join(app.getAppPath(), 'frontend', 'dist', 'index.html'))
  }

  return win
}

// 启动后端进程
function startBackend() {
  if (backendProcess) return

  const isWindows = process.platform === 'win32'
  const pythonCmd = isWindows ? 'python' : 'python3'

  // In production, backend is in extraResources; in dev, it's relative to project root
  const backendPath = isDev
    ? path.join(__dirname, '..', 'backend')
    : path.join(process.resourcesPath, 'backend')

  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: backendPath,
    stdio: ['ignore', 'pipe', 'pipe']
    // No shell: true — avoids orphan process on Windows
  })

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data}`)
  })

  backendProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data}`)
  })

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend process:', err)
  })

  backendProcess.on('exit', (code) => {
    console.log(`Backend process exited with code ${code}`)
    backendProcess = null
  })

  console.log('Backend process started')
}

// 停止后端进程
function stopBackend() {
  if (backendProcess) {
    const proc = backendProcess
    backendProcess = null

    if (process.platform === 'win32') {
      // On Windows, use taskkill to kill the process tree
      spawn('taskkill', ['/pid', String(proc.pid), '/f', '/t'])
    } else {
      proc.kill('SIGTERM')
    }

    console.log('Backend process stopped')
  }
}

// IPC 处理程序
ipcMain.handle('save-file-dialog', async () => {
  const result = await dialog.showSaveDialog({
    title: '导出 PNG 序列',
    defaultPath: 'animancer_export.zip',
    filters: [
      { name: 'ZIP Archive', extensions: ['zip'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  return result
})

ipcMain.handle('open-file-dialog', async () => {
  const result = await dialog.showOpenDialog({
    title: '选择图片',
    filters: [
      { name: 'Images', extensions: ['jpg', 'jpeg', 'png'] },
      { name: 'All Files', extensions: ['*'] }
    ],
    properties: ['openFile']
  })
  return result
})

app.whenReady().then(() => {
  const win = createWindow()

  // 生产环境启动后端
  if (!isDev) {
    startBackend()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
  // On macOS, keep backend running until app actually quits
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    const win = createWindow()
    if (!isDev) {
      startBackend()
    }
  }
})

app.on('before-quit', () => {
  stopBackend()
})
