import { useEffect, useRef, useState } from 'react'
import * as d3 from "d3"

const AnimatedCircles = () => {
    function generateCircles() {
        const result = []
        for (let i = 0; i < 6; i++) {
            if (Math.random() > 0.5) {
                result.push(i)
            }
        }
        return result
    }

    const [dataset, setDataset] = useState(generateCircles())
    const ref = useRef()

    useEffect(() => {
        const interval = setInterval(() => setDataset(generateCircles()), 1000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        const svgElement = d3.select(ref.current)
        svgElement.selectAll("circle")
            .data(dataset, d => d)
            .join(
                enter => (
                    enter.append("circle")
                        .attr("cx", it => it * 15 + 10)
                        .attr("cy", 10)
                        .attr("r", 0)
                        .attr("fill", "cornflowerblue")
                        .call(enter => (
                            enter.transition().duration(600).attr("r", 6).style("opacity", 1)
                        ))
                ),
                update => (update.transition().duration(600).attr("fill", "lightgrey")),
                exit => (exit.attr("fill", "tomato")
                    .call(exit => (exit.transition().duration(600).attr("r", 0).style("opacity", 0).remove())))
            )

    }, [dataset])

    return <svg
        viewBox="0 0 100 20"
        ref={ref}>
    </svg>
}

export default AnimatedCircles
