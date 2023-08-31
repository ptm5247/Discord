const spawn = require('child_process').spawn
const server = spawn('python', ['server.py'], {detached: true})
const { app, BrowserWindow } = require('electron')

server.stderr.pipe(process.stdout)

const createWindow = () => {
  const win = new BrowserWindow({width: 800, height: 600})
  win.loadURL('http://localhost:8080/index.html')
  win.setMenuBarVisibility(false)

  server.on('exit', app.exit)
  app.on('window-all-closed', () => server.kill('SIGTERM'))
}

app.whenReady().then(createWindow)
