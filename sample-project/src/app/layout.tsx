import './globals.css'

export const metadata = {
  title: 'Sample Next.js App',
  description: 'Testing quality gate system',
}

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
