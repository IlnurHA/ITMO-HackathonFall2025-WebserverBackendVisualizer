import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import './App.css'
import Header from './Header'
import GraphPage from './pages/GraphPage'
import CFGVisualizer from './pages/CFGVisualizer'

function App() {
  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header />
        <Routes>
          <Route path="/" Component={CFGVisualizer} />
          <Route path="/graph" Component={GraphPage} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
