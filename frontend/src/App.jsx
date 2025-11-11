import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import './App.css'
import Header from './Header'
import Home from './pages/Home'
import RandomCircles from './pages/RandomCircles'
import AnimatedCircles from './pages/AnimatedCircles'

function App() {
  return (
    <Router>
      <div>
        <Header />
        <Routes>
          <Route path="/" Component={Home} />
          <Route path="/random-circles" Component={RandomCircles} />
          <Route path="/animated-circles" Component={AnimatedCircles} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
