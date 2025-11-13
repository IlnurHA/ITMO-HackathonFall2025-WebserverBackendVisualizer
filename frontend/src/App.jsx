import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import './App.css'
import Header from './Header'
import Home from './pages/Home'
import RandomCircles from './pages/RandomCircles'
import AnimatedCircles from './pages/AnimatedCircles'
import TreePage from './pages/TreePage'
import CFGVisualizer from './pages/CFGVisualizer'

function App() {
  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/random-circles" element={<RandomCircles />} />
          <Route path="/animated-circles" element={<AnimatedCircles />} />
          <Route path="/tree" element={<TreePage />} />
          <Route path="/cfg-visualizer" element={<CFGVisualizer />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App