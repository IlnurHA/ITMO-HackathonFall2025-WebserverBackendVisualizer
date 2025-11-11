import { useEffect, useRef, useState } from 'react'

const RandomCircles = () => {
    const [dataset, setDataset] = useState(
        Array.from({ length: 10 }, (_, i) => [i * 30 + 15, i * 30 + 15])
    )
    const ref = useRef()

    useEffect(() => {
        const interval = setInterval(() => {
            const newDataset = Array.from({ length: 10 }, () => [
                Math.random() * 300,
                Math.random() * 300
            ])
            setDataset(newDataset)
        }, 500)
        return () => clearInterval(interval)
    }, [])

    return <svg
        viewBox="0 0 300 300"
        ref={ref}
    >
        {dataset.map(([x, y], i) => (
            <circle
                key={i}
                cx={x}
                cy={y}
                r="10"
                fill="green"
            />
        ))}
    </svg>
}

export default RandomCircles