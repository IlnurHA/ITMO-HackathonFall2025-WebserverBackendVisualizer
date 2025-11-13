import { useLayoutEffect, useState, useRef, useEffect } from "react"
import * as d3 from "d3"
import tmpData from "./sample.json"
import { createRoot } from "react-dom/client"


const RADIUS = 150;
const LINK_DISTANCE = 400;
const FORCE_RADIUS_FACTOR = 1;
const NODE_STRENGTH = 1;

function transformedData(json) {
    const nodes = [{ id: "root" }]
    const links = []

    json.modules.forEach(it => {
        nodes.push({ id: it.module, type: "module" })
        links.push({ source: "root", target: it.module })
        it.tree.children.forEach(child => {
            nodes.push({ id: child.name, type: child.type })
            links.push({ source: it.module, target: child.name })
            child.calls.forEach(call => {
                links.push({ source: child.name, target: call.function, strength: 0 })
            });
        });
    })

    return { nodes, links }
}

const computeGraphDistances = (nodes, links) => {
    // Build adjacency list without modifying the input
    const graph = {};
    nodes.forEach((node) => {
        graph[node.id] = [];
    });

    links.forEach((link) => {
        graph[link.source.id].push(link.target.id);
        graph[link.target.id].push(link.source.id);
    });

    // BFS for all nodes
    const distances = {};

    nodes.forEach((node) => {
        const queue = [node.id];
        const visited = new Set([node.id]);
        const dist = { [node.id]: 0 };

        while (queue.length > 0) {
            const current = queue.shift();
            const neighbors = graph[current];

            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    dist[neighbor] = dist[current] + 1;
                    queue.push(neighbor);
                }
            }
        }

        distances[node.id] = dist;
    });

    return distances;
};


const GraphPage = () => {
    const [dataset, setDataset] = useState(transformedData(tmpData))
    const hoveredNodeIdRef = useRef(null)
    const ref = useRef(null)
    const containerRef = useRef(null)
    const [width, setWidth] = useState(0)
    const [height, setHeight] = useState(0)
    const gRef = useRef(null) // Ref to store the g element
    const simulationRef = useRef(null) // Ref to store the simulation

    // file loading
    const handleFileChange = (event) => {
        const file = event.target.files[0];

        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const data = JSON.parse(content);

                    setDataset(transformedData(data))
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                }
            };
            reader.readAsText(file);
        }
    }

    useLayoutEffect(() => {
        const container = containerRef.current
        const svg = ref.current

        if (!container || !svg) return

        const width = container.clientWidth
        const height = container.clientHeight

        setWidth(width)
        setHeight(height)

        svg.setAttribute("width", width)
        svg.setAttribute("height", height)
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`)

        // Initialize the g element if it doesn't exist
        if (!gRef.current) {
            gRef.current = d3.select(ref.current).append("g").attr("cursor", "grab")
            d3.select(ref.current).call(d3.zoom()
                .extent([[0, 0], [width, height]])
                .on("zoom", zoomed))
        }

        function zoomed({ transform }) {
            if (gRef.current) {
                gRef.current.attr("transform", transform)
            }
        }
    }, [])

    // Initialize the simulation and graph
    useEffect(() => {
        if (!gRef.current || !dataset.nodes || !dataset.links) return

        // Destroy the previous simulation if it exists
        // if (simulationRef.current) {
        //     simulationRef.current.stop()
        // }

        // Create a new simulation
        simulationRef.current = d3.forceSimulation(dataset.nodes)
            .force("link", d3.forceLink(dataset.links).id(d => d.id).distance(LINK_DISTANCE))
            .force("charge", d3.forceManyBody().strength(d => d.strength * NODE_STRENGTH))
            .force("collision", d3.forceCollide(RADIUS * FORCE_RADIUS_FACTOR))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))

        const linksSelection = gRef.current
            .selectAll("line.link")
            .data(dataset.links, l => l.source + l.target)
            .join(
                enter => (enter.append("line")
                    .classed("link", true)
                    .attr("stroke", "black")
                    .attr("zx", -1)),
                update => update,
                exit => exit.remove()
            )

        const nodesSelection = gRef.current
            .selectAll("foreignObject.node")
            .data(dataset.nodes, n => n.id)
            .join(
                enter => (enter.append("foreignObject")
                    .classed("node", true)
                    .attr("width", 1)
                    .attr("height", 1)
                    .attr("overflow", "visible")),
                update => update,
                exit => exit.remove()
            )

        // rendering
        nodesSelection?.each(function (node) {
            function Node({ node }) {
                return (
                    <div className="bg-blue-300 rounded-full border border-blue-800 px-2 z-20">
                        <h3>{node.id}</h3>
                        {node.type}
                    </div>
                );
            }
            const root = createRoot(this)
            root.render(
                <div className="fixtranslate" >
                    <Node node={node} />
                </div>,
            );
        });

        const onMouseOver = (event, d) => {
            hoveredNodeIdRef.current = d.id
            // Highlight the edges connected to this node
            linksSelection
                .filter(link => link.source.id === d.id || link.target.id === d.id)
                .attr("stroke", "red")
        }

        const onMouseOut = (event, d) => {
            hoveredNodeIdRef.current = null
            // Revert the stroke color and width
            linksSelection
                .filter(link => link.source.id === d.id || link.target.id === d.id)
                .attr("stroke", "black")
        }
        // hover
        nodesSelection
            .on("mouseover", onMouseOver)
            .on("mouseout", onMouseOut)

        const graphDistances = computeGraphDistances(dataset.nodes, dataset.links)

        simulationRef.current.on("tick", () => {
            linksSelection
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y)

            nodesSelection.attr("transform", (d) => `translate(${d.x}, ${d.y})`)

            if (hoveredNodeIdRef.current) {
                linksSelection
                    .style("opacity", (d) => {
                        const distance = graphDistances[hoveredNodeIdRef.current][d.target.id] || graphDistances[hoveredNodeIdRef.current][d.source.id];
                        const maxDistance = 3; // Adjust based on your graph
                        const opacity = 1 - (distance / maxDistance);
                        return Math.max(0.1, opacity); // Ensure minimum opacity
                    });

                // Apply opacity to nodes
                nodesSelection
                    .transition().duration(50)
                    .style("opacity", (d) => {
                        if (d.id === hoveredNodeIdRef.current) return 1; // Keep hovered node fully visible
                        const distance = graphDistances[hoveredNodeIdRef.current][d.id];
                        const maxDistance = 3; // Adjust based on your graph
                        const opacity = 1 - (distance / maxDistance);
                        return Math.max(0.1, opacity); // Ensure minimum opacity
                    });
            } else {
                // Reset opacity if no node is hovered
                linksSelection.style("opacity", 1)
                nodesSelection.style("opacity", 1)
            }
        })

        nodesSelection.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
    }, [dataset, height, width])

    // Drag functions
    function dragstarted(event) {
        if (!event.active) simulationRef.current.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
    }

    function dragged(event) {
        event.subject.fx = event.x
        event.subject.fy = event.y
    }

    function dragended(event) {
        if (!event.active) simulationRef.current.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
    }

    return (
        <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
            <input type="file" accept=".json" onChange={handleFileChange} />
            <div ref={containerRef} style={{ height: "100%", width: "100%" }}>
                <svg ref={ref} height={height} width={width} />
            </div>
        </div>
    )
}

export default GraphPage