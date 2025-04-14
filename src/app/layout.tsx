// app/layout.tsx
import './globals.css'
import { Inter, Poppins } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-poppins',
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
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${poppins.variable} min-h-screen bg-gradient-to-br from-background-start to-background-end antialiased`}>
        {children}
      </body>
    </html>
  )
}
