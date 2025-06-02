const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  if (isDev) {
    win.loadURL('http://localhost:3000');
  } else {
    win.loadFile(path.join(__dirname, 'build/index.html'));
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    // Antes de cerrar la app, limpiar sesión de pacientes
    axios.post('http://127.0.0.1:8000/clear_session')
      .catch(() => { /* ignorar errores */ })
      .finally(() => {
        if (process.platform !== 'darwin') {
          app.quit();
        }
      });
  });

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
