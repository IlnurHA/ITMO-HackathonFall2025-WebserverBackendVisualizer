import { useState, useEffect } from "react"

const Home = () => {
    const [data, setData] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetch("http://localhost:8000/graph")
            .then(response => {
                return response.json()
            })
            .then(data => {
                setData(data)
            })
            .catch(error => {
                setError(error.message)
            })
    }, [])
    return <div>
        <h1>Testing request to backend</h1>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
}

export default Home