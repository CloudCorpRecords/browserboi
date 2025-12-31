const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onLog: (callback) => ipcRenderer.on('log-message', (_event, value) => callback(value))
});
