import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import './App.css'
import Header from './Header'
import Home from './pages/Home'
import RandomCircles from './pages/RandomCircles'
import AnimatedCircles from './pages/AnimatedCircles'
import TreePage from './pages/TreePage'

function App() {
  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header />
        <Routes>
          <Route path="/" Component={Home} />
          <Route path="/random-circles" Component={RandomCircles} />
          <Route path="/animated-circles" Component={AnimatedCircles} />
          <Route path="/tree" Component={TreePage} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
