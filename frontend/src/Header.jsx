import { Link } from 'react-router-dom'

const Header = () => {
    return <header>
        <nav>
            <Link to="/">Tree</Link>
            <Link to="/graph">Graph</Link>
        </nav>
    </header>
}

export default Header