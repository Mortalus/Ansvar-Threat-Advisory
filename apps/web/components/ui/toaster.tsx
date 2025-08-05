'use client'

import { useToast } from '@/hooks/use-toast'

export function Toaster() {
  const { toasts } = useToast()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="px-4 py-3 rounded-lg shadow-lg bg-gray-800 text-white border border-gray-700"
        >
          {toast.title && <div className="font-semibold">{toast.title}</div>}
          {toast.description && <div className="text-sm mt-1">{toast.description}</div>}
        </div>
      ))}
    </div>
  )
}
