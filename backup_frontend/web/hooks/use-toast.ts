import { useState, useEffect } from 'react'

type Toast = {
  id: string
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
}

let toastCount = 0
const toasts: Toast[] = []
const listeners: ((toasts: Toast[]) => void)[] = []

function emitChange() {
  for (let listener of listeners) {
    listener(toasts)
  }
}

export function toast(props: Omit<Toast, 'id'>) {
  const id = String(++toastCount)
  const toast = { ...props, id }
  toasts.push(toast)
  emitChange()
  
  setTimeout(() => {
    const index = toasts.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.splice(index, 1)
      emitChange()
    }
  }, 5000)
  
  return { id }
}

export function useToast() {
  const [, setVersion] = useState(0)
  
  useEffect(() => {
    const listener = () => setVersion(v => v + 1)
    listeners.push(listener)
    return () => {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [])
  
  return { toasts, toast }
}
