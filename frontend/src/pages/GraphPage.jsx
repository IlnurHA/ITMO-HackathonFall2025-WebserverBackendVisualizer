import { useLayoutEffect, useState, useRef, useEffect } from "react"
import * as d3 from "d3"
import tmpData from "./sample.json"
import { createRoot } from "react-dom/client"


const RADIUS = 350;
const LINK_DISTANCE = 300;
const FORCE_RADIUS_FACTOR = 0.2;
const NODE_STRENGTH = 0.001;

function transformedData(json, expandedNodes = new Set()) {
    const nodes = [{
        id: "root",
        type: "root",
        level: 0,
        hasChildren: json.dependencies.modules && json.dependencies.modules.length > 0
    }]
    const links = []

    // Always show modules when root is expanded
    if (expandedNodes.has("root") || expandedNodes.size === 0) {
        json.dependencies.modules.forEach(module => {
            const moduleNode = {
                id: module.module,
                type: "module",
                level: 1,
                hasChildren: module.tree && module.tree.children && module.tree.children.length > 0,
                originalId: module.module
            }
            nodes.push(moduleNode)
            links.push({ source: "root", target: module.module })

            // Show children if module is expanded
            if (expandedNodes.has(module.module)) {
                module.tree.children.forEach(child => {
                    const childNode = {
                        id: child.name,
                        type: child.type,
                        level: 2,
                        hasChildren: child.calls && child.calls.length > 0,
                        originalId: child.name,
                        parent: module.module
                    }
                    nodes.push(childNode)
                    links.push({ source: module.module, target: child.name })

                    // Show calls if child is expanded
                    if (expandedNodes.has(child.name)) {
                        child.calls.forEach(call => {
                            links.push({
                                source: child.name,
                                target: call.function,
                                strength: 0,
                                isCall: true,
                                parent: child.name
                            })
                        })
                    }
                })
            }
        })
    }

    return { nodes, links }
}

const computeGraphDistances = (nodes, links) => {
    const graph = {};
    nodes.forEach((node) => {
        graph[node.id] = [];
    });

    links.forEach((link) => {
        if (link.source.id) {
            graph[link.source.id].push(link.target.id);
            graph[link.target.id].push(link.source.id);
        }
    });

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

// Node component for rendering individual nodes
const GraphNode = ({ node, isExpanded, onToggle }) => {
    return (
        <div className={`graph-node graph-node--${node.type}`}>
            <h3 className="node-title">{node.id}</h3>
            <p className="node-type">{node.type}</p>
            {node.hasChildren && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onToggle(node.id);
                    }}
                    className="expand-button-bottom"
                    title={isExpanded ? "Collapse" : "Expand"}
                >
                    {isExpanded ? "collapse" : "expand"}
                </button>
            )}
        </div>
    );
};

const GraphPage = () => {
    const [dataset, setDataset] = useState(null)
    const [expandedNodes, setExpandedNodes] = useState(new Set(["root"])) // Start with root expanded
    const [loadedData, setLoadedData] = useState(null) // Add state to store loaded data
    const hoveredNodeIdRef = useRef(null)
    const ref = useRef(null)
    const containerRef = useRef(null)
    const [width, setWidth] = useState(0)
    const [height, setHeight] = useState(0)
    const gRef = useRef(null)
    const simulationRef = useRef(null)
    const nodePositionsRef = useRef(new Map()) // Store node positions
    const [repoPath, setRepoPath] = useState("")
    const [includeTests, setIncludeTests] = useState(false)


    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch("http://localhost:8000/scan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    repo_root: repoPath,
                    include_tests: includeTests,
                    max_depth: 3
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server returned status ${response.status}`);
            }

            const result = await response.json();
            console.log("ping");

            setLoadedData(result);
        } catch (err) {
            console.error("Error:", err);
        }
    };

    // Toggle node expansion/collapse
    const toggleNode = (nodeId) => {
        setExpandedNodes(prev => {
            const newExpanded = new Set(prev);
            if (newExpanded.has(nodeId)) {
                newExpanded.delete(nodeId);
                // Also collapse all descendants
                const toRemove = [];
                for (const node of newExpanded) {
                    if (node.startsWith(nodeId + ".")) {
                        toRemove.push(node);
                    }
                }
                toRemove.forEach(n => newExpanded.delete(n));
            } else {
                newExpanded.add(nodeId);
            }
            return newExpanded;
        });
    };

    // Expand all nodes
    const expandAll = () => {
        const allNodeIds = new Set();
        const collectNodes = (obj, prefix = "") => {
            if (obj.modules) {
                obj.modules.forEach(module => {
                    const moduleId = module.module;
                    allNodeIds.add(moduleId);
                    if (module.tree && module.tree.children) {
                        module.tree.children.forEach(child => {
                            allNodeIds.add(child.name);
                            if (child.calls) {
                                child.calls.forEach(call => {
                                    allNodeIds.add(call.function);
                                });
                            }
                        });
                    }
                });
            }
        };
        collectNodes(tmpData);
        allNodeIds.add("root");
        setExpandedNodes(allNodeIds);
    };

    // Collapse all nodes
    const collapseAll = () => {
        setExpandedNodes(new Set(["root"]));
    };

    // file loading
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const data = JSON.parse(content);
                    setLoadedData(data) // Store the loaded data
                    setDataset(transformedData(data, expandedNodes))
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                }
            };
            reader.readAsText(file);
        }
    }

    // Store current node positions before dataset changes
    const storeNodePositions = () => {
        if (simulationRef.current && dataset.nodes) {
            dataset.nodes.forEach(node => {
                if (node.x !== undefined && node.y !== undefined) {
                    nodePositionsRef.current.set(node.id, { x: node.x, y: node.y });
                }
            });
        }
    };

    // Apply stored positions to new nodes
    const applyStoredPositions = (nodes) => {
        nodes.forEach(node => {
            const storedPos = nodePositionsRef.current.get(node.id);
            if (storedPos) {
                node.x = storedPos.x;
                node.y = storedPos.y;
                node.vx = 0; // Reset velocity to prevent jumping
                node.vy = 0;
            }
        });
    };

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

    // Update dataset when expanded nodes change
    useEffect(() => {
        if (loadedData == null) return;
        storeNodePositions(); // Store positions before updating dataset
        const newDataset = transformedData(loadedData, expandedNodes);
        applyStoredPositions(newDataset.nodes); // Apply stored positions to new nodes
        setDataset(newDataset);
        console.log("pong");

    }, [expandedNodes, loadedData]); // Added loadedData to dependencies

    // Initialize the simulation and graph
    useEffect(() => {
        if (dataset == null) return;
        if (!gRef.current || !dataset.nodes || !dataset.links) return

        if (simulationRef.current) {
            simulationRef.current.stop()
        }

        // Create a more stable simulation by preserving some momentum
        simulationRef.current = d3.forceSimulation(dataset.nodes)
            .force("link", d3.forceLink(dataset.links).id(d => d.id).distance(LINK_DISTANCE))
            .force("charge", d3.forceManyBody().strength(d => d.strength * NODE_STRENGTH))
            .force("collision", d3.forceCollide(RADIUS * FORCE_RADIUS_FACTOR))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.02)) // Reduced strength

        // Create separate groups for links and nodes to ensure proper layering
        const linksGroup = gRef.current.selectAll("g.links-group").data([null])
            .join("g")
            .attr("class", "links-group")

        const nodesGroup = gRef.current.selectAll("g.nodes-group").data([null])
            .join("g")
            .attr("class", "nodes-group")

        const linksSelection = linksGroup
            .selectAll("line.link")
            .data(dataset.links, l => `${l.source.id || l.source}-${l.target.id || l.target}`)
            .join(
                enter => (enter.append("line")
                    .classed("link", true)
                    .attr("stroke", d => d.isCall ? "#666" : "black")
                    .attr("stroke-width", d => d.isCall ? 1 : 2)),
                update => update,
                exit => exit.remove()
            )

        const nodesSelection = nodesGroup
            .selectAll("foreignObject.node")
            .data(dataset.nodes, n => n.id)
            .join(
                enter => (enter.append("foreignObject")
                    .classed("node", true)
                    .classed("node--root", d => d.type === "root")
                    .classed("node--module", d => d.type === "module")
                    .classed("node--class", d => d.type === "class")
                    .classed("node--function", d => d.type === "function")
                    .attr("width", 1)
                    .attr("height", 1)
                    .attr("overflow", "visible")),
                update => update,
                exit => exit.remove()
            )

        // Clean up previous React roots
        nodesSelection.each(function () {
            if (this._reactRoot) {
                this._reactRoot.unmount();
            }
        });

        // rendering
        nodesSelection.each(function (node) {
            const isExpanded = expandedNodes.has(node.id);
            const root = createRoot(this);
            this._reactRoot = root;

            root.render(
                <GraphNode
                    node={node}
                    isExpanded={isExpanded}
                    onToggle={toggleNode}
                />
            );
        });

        const onMouseOver = (event, d) => {
            hoveredNodeIdRef.current = d.id
            linksSelection
                .filter(link => (link.source.id === d.id || link.target.id === d.id))
                .attr("stroke", "red")
                .attr("stroke-width", 3)
        }

        const onMouseOut = (event, d) => {
            hoveredNodeIdRef.current = null
            linksSelection
                .filter(link => (link.source.id === d.id || link.target.id === d.id))
                .attr("stroke", d => d.isCall ? "#666" : "black")
                .attr("stroke-width", d => d.isCall ? 1 : 2)
        }

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
                        const maxDistance = 3;
                        const opacity = 1 - (distance / maxDistance);
                        return Math.max(0.1, opacity);
                    });

                nodesSelection
                    .transition().duration(50)
                    .style("opacity", (d) => {
                        if (d.id === hoveredNodeIdRef.current) return 1;
                        const distance = graphDistances[hoveredNodeIdRef.current][d.id];
                        const maxDistance = 3;
                        const opacity = 1 - (distance / maxDistance);
                        return Math.max(0.1, opacity);
                    });
            } else {
                linksSelection.style("opacity", 1)
                nodesSelection.style("opacity", 1)
            }
        })

        nodesSelection.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))

        // Reduce initial alpha to make movement smoother
        simulationRef.current.alpha(0.3).restart();
    }, [dataset, height, width, expandedNodes])

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
            {/* Navigation Controls */}
            <div className="nav-controls">
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <input
                        type="file"
                        accept=".json"
                        onChange={handleFileChange}
                        className="file-input"
                    />
                    <form onSubmit={handleSubmit} className="path-form">
                        <label htmlFor="repoPath">Путь к репозиторию:</label>
                        <input
                            id="repoPath"
                            type="text"
                            value={repoPath}
                            onChange={(e) => setRepoPath(e.target.value)}
                            placeholder="/path/to/your/project"
                            required
                            className="path-input"
                        />
                        <input
                            id="includeTests"
                            type="checkbox"
                            checked={includeTests}
                            onChange={(e) => setIncludeTests(e.target.checked)}
                        />
                        <label htmlFor="includeTests">Включить тестовые зависимости</label>
                        <button
                            type="submit"
                            className="analyze-button"
                        >Загрузить</button>
                    </form>
                    <button
                        onClick={expandAll}
                        className="btn btn-expand"
                    >
                        Expand All
                    </button>
                    <button
                        onClick={collapseAll}
                        className="btn btn-collapse"
                    >
                        Collapse All
                    </button>
                    <div className="expanded-info">
                        Expanded: {expandedNodes.size} nodes
                    </div>
                </div>
            </div>

            <div ref={containerRef} style={{ height: "calc(100vh - 80px)", width: "100%" }}>
                <svg ref={ref} height={height} width={width} />
            </div>
        </div>
    )
}

export default GraphPage