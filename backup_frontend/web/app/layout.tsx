import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from '@/components/ui/toaster'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Ansvar Threat Advisory',
  description: 'AI-powered threat modeling and security analysis platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/svg+xml" href="/ansvar-logo.svg" />
        <link rel="alternate icon" href="/favicon.ico" />
      </head>
      <body className={inter.className}>
        <header className="w-full border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
          <div className="mx-auto max-w-7xl px-4 py-2 flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-3">
              <Link href="/" className="font-medium text-gray-800 hover:text-blue-600">Ansvar</Link>
              <span className="text-gray-300">|</span>
              <Link href="/workflows" className="hover:text-blue-600">Workflows</Link>
              <Link href="/admin" className="hover:text-blue-600">Admin</Link>
            </div>
            <AuthStatusBar />
          </div>
        </header>
        <main className="min-h-[calc(100vh-48px)]">{children}</main>
        <Toaster />
      </body>
    </html>
  )
}

/* Client component in the same file for a minimal status bar */
function AuthStatusBar() {
  if (typeof window === 'undefined') return null as any
  const token = typeof window !== 'undefined' ? localStorage.getItem('session_token') : null
  const userRaw = typeof window !== 'undefined' ? localStorage.getItem('user_data') : null
  let username = ''
  try { username = userRaw ? JSON.parse(userRaw).username : '' } catch {}
  return (
    <div className="flex items-center gap-3">
      {token ? (
        <>
          <span className="text-gray-700">Signed in{username ? ` as ${username}` : ''}</span>
          <button
            className="px-2 py-1 rounded border hover:bg-gray-50"
            onClick={() => { localStorage.removeItem('session_token'); localStorage.removeItem('user_data'); window.location.href = '/login' }}
          >Logout</button>
        </>
      ) : (
        <Link href="/login" className="px-2 py-1 rounded border hover:bg-gray-50">Login</Link>
      )}
    </div>
  )
}
