import { Link } from 'react-router-dom'

const Header = () => {
    return <header>
        <nav>
            <Link to="/">Home</Link>
            <Link to="/random-circles">Random Circles</Link>
            <Link to="/animated-circles">Animated Circles</Link>
            <Link to="/tree">Tree</Link>
            <Link to="/graph">Graph</Link>
        </nav>
    </header>
}

export default Header