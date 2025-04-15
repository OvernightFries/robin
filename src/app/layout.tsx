// app/layout.tsx
import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata = {
  title: 'Robin AI - Financial Assistant',
  description: 'Your intelligent financial market assistant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable}`}>
      <body className="min-h-screen bg-wizard-background text-wizard-text-primary antialiased">
        {children}
      </body>
    </html>
  )
}
