import './globals.css'

export const metadata = {
  title: 'Sample Next.js App',
  description: 'Testing quality gate system',
}

// Configuration from environment variables
const isDevelopment = process.env.NODE_ENV === 'development'
const analyticsId = process.env.ANALYTICS_ID
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3000'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
