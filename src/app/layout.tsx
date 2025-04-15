// app/layout.tsx
import './globals.css'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'

export const metadata = {
  title: 'Robin - AI Trading Assistant',
  description: 'Your intelligent companion for market analysis and trading insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="min-h-screen bg-wizard-background text-wizard-text-primary antialiased">
        {children}
      </body>
    </html>
  )
}
