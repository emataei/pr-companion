import React from 'react'
import './globals.css'

export const metadata = {
  title: 'PR Companion App',
  description: 'A simple Next.js app for testing PR workflows',
}

interface RootLayoutProps {
  readonly children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
