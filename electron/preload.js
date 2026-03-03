const { contextBridge, ipcRenderer } = require('electron')

// 白名单模式：只允许预定义的 IPC channels
const VALID_SEND_CHANNELS = ['save-file-dialog', 'open-file-dialog']
const VALID_RECEIVE_CHANNELS = ['file-selected', 'dialog-closed']

// Store mapping from user callbacks to wrapper functions for proper removal
const listenerMap = new Map()

contextBridge.exposeInMainWorld('electronAPI', {
  // 调用主进程方法（返回 Promise）
  invoke: async (channel, ...args) => {
    if (VALID_SEND_CHANNELS.includes(channel)) {
      return await ipcRenderer.invoke(channel, ...args)
    }
    throw new Error(`Invalid IPC channel: ${channel}`)
  },

  // 监听主进程消息
  on: (channel, callback) => {
    if (VALID_RECEIVE_CHANNELS.includes(channel)) {
      const wrapper = (event, ...args) => callback(...args)
      listenerMap.set(callback, wrapper)
      ipcRenderer.on(channel, wrapper)
    }
  },

  // 移除监听器
  removeListener: (channel, callback) => {
    if (VALID_RECEIVE_CHANNELS.includes(channel)) {
      const wrapper = listenerMap.get(callback)
      if (wrapper) {
        ipcRenderer.removeListener(channel, wrapper)
        listenerMap.delete(callback)
      }
    }
  }
})
