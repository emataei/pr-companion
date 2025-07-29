export default function Home() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>PR Companion App</h1>
      <p>Welcome to the PR Companion testing application!</p>
      
      <div style={{ marginTop: '2rem' }}>
        <h2>Features to Test:</h2>
        <ul>
          <li>Code quality analysis</li>
          <li>PR visual generation</li>
          <li>Documentation suggestions</li>
          <li>AI-powered reviews</li>
        </ul>
      </div>
      
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h3>Test Component</h3>
        <p>This is a simple component to test the workflow automation.</p>
      </div>
    </main>
  )
}
