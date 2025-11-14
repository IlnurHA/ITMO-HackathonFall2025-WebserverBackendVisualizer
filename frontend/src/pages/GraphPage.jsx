import { useLayoutEffect, useState, useRef, useEffect } from "react"
import * as d3 from "d3"
import { createRoot } from "react-dom/client"

function transformedData(json, expandedNodes = new Set()) {
    const nodes = [{
        id: "root",
        name: "root",
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
                name: module.module,
                type: "module",
                level: 1,
                hasChildren: module.tree && module.tree.children && module.tree.children.length > 0,
                originalId: module.module
            }
            nodes.push(moduleNode)
            links.push({ source: "root", target: module.module, len_c: 2, strength: 0.2 })

            // Show children if module is expanded
            if (expandedNodes.has(module.module)) {
                module.tree.children.forEach(child => {
                    const childId = `${module.module}.${child.name}` // Make unique
                    const childNode = {
                        id: childId,
                        name: child.name,
                        type: child.type,
                        level: 2,
                        hasChildren: child.calls && child.calls.length > 0,
                        originalId: child.name,
                        parent: module.module
                    }
                    nodes.push(childNode)
                    links.push({ source: module.module, target: childId, len_c: 0.5 })

                    // Show calls if child is expanded
                    if (expandedNodes.has(childId)) {
                        child.calls.forEach(call => {
                            const callId = `${childId}.${call.function}`
                            links.push({
                                source: childId,
                                target: callId,
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

// Node component for rendering individual nodes
const GraphNode = ({ node, isExpanded, onToggle }) => {
    return (
        <div className={`graph-node graph-node--${node.type}`}>
            <h3 className="node-title">{node.name}</h3>
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
    const [clusterSpecialTypes, setClusterSpecialTypes] = useState(true) // Add toggle for clustering
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

    // Force parameters with sliders
    const [linkDistance, setLinkDistance] = useState(400)
    const [linkStrength, setLinkStrength] = useState(0.5)
    const [nodeRepulsion, setNodeRepulsion] = useState(-1)
    const [collisionRadius, setCollisionRadius] = useState(70)
    const [clusterStrength, setClusterStrength] = useState(0.1)
    const [moduleRadialStrength, setModuleRadialStrength] = useState(0.15)
    const [centerStrength, setCenterStrength] = useState(0.02)


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
        const allNodeIds = new Set(dataset.nodes.map(it => it.id));
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

        // Custom force to cluster handler and sql_class nodes
        const clusterForce = () => {
            if (!clusterSpecialTypes) return;

            const handlerNodes = dataset.nodes.filter(n => n.type === 'handler');
            const sqlClassNodes = dataset.nodes.filter(n => n.type === 'sql_class');

            // Define cluster centers (adjust positions as needed)
            const handlerCenter = { x: width * 0.25, y: height * 0.75 };
            const sqlClassCenter = { x: width * 0.75, y: height * 0.75 };

            handlerNodes.forEach(node => {
                node.vx += (handlerCenter.x - node.x) * clusterStrength;
                node.vy += (handlerCenter.y - node.y) * clusterStrength;
            });

            sqlClassNodes.forEach(node => {
                node.vx += (sqlClassCenter.x - node.x) * clusterStrength;
                node.vy += (sqlClassCenter.y - node.y) * clusterStrength;
            });
        };

        // Custom force to arrange modules radially around root
        const moduleRadialForce = () => {
            const modules = dataset.nodes.filter(n => n.type === 'module');
            const root = dataset.nodes.find(n => n.type === 'root');

            if (!root || modules.length === 0) return;

            const radius = 300; // Distance from root to modules
            const angleStep = (2 * Math.PI) / modules.length;

            modules.forEach((node, i) => {
                const targetAngle = i * angleStep;
                const targetX = root.x + Math.cos(targetAngle) * radius;
                const targetY = root.y + Math.sin(targetAngle) * radius;

                node.vx += (targetX - node.x) * moduleRadialStrength;
                node.vy += (targetY - node.y) * moduleRadialStrength;
            });
        };

        // Create simulation with type-specific forces
        simulationRef.current = d3.forceSimulation(dataset.nodes)
            .force("link", d3.forceLink(dataset.links)
                .id(d => d.id)
                .distance(d => {
                    // Longer links for modules to root
                    if (d.source.type === 'root' || d.target.type === 'root') return 3;
                    // Shorter links for children
                    return (d.len_c || 1) * linkDistance;
                })
                .strength(d => {
                    // Weaker links to special types if clustering
                    if (clusterSpecialTypes && (d.target.type === 'handler' || d.target.type === 'sql_class')) {
                        return 0.1;
                    }
                    return d.strength !== undefined ? d.strength : linkStrength;
                })
            )
            .force("charge", d3.forceManyBody()
                .strength(d => {
                    // Stronger repulsion for modules
                    if (d.type === 'module') return -8;
                    // Weaker for handler/sql_class if clustering
                    if (clusterSpecialTypes && (d.type === 'handler' || d.type === 'sql_class')) return -50;
                    return d.strength * 0.001 || nodeRepulsion;
                })
            )
            .force("collision", d3.forceCollide()
                .radius(d => {
                    // Larger collision radius for modules
                    if (d.type === 'module') return collisionRadius * 0.4;
                    return collisionRadius;
                })
            )
            .force("center", d3.forceCenter(width / 2, height / 2).strength(centerStrength))
            .force("moduleRadial", moduleRadialForce)
            .force("cluster", clusterForce);

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
                enter => {
                    const line = enter.append("line")
                        .attr("stroke", "black")
                        .attr("stroke-width", 1)
                        .classed("link", true)
                    return line;
                },
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
                    .classed("node--handler", d => d.type == "handler")
                    .classed("node--sql_class", d => d.type === "sql_class")
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
                .attr("stroke", "#e74c3c") // Bright red for highlighted links
                .attr("stroke-width", 2)
                .style("opacity", 1)
                .attr("stroke-dasharray", null); // Remove dashes on hover

            // Dim unrelated links
            linksSelection
                .filter(link => (link.source.id !== d.id && link.target.id !== d.id))
                .style("opacity", 0.2);

            // Highlight connected nodes
            nodesSelection
                .filter(node => node.id === d.id)
                .style("opacity", 1);

            nodesSelection
                .filter(node => {
                    if (node.id === d.id) return false;
                    return linksSelection
                        .filter(link => (link.source.id === d.id || link.target.id === d.id))
                        .data()
                        .some(link => link.source.id === node.id || link.target.id === node.id);
                })
                .style("opacity", 0.8);

            // Dim unrelated nodes
            nodesSelection
                .filter(node => {
                    if (node.id === d.id) return false;
                    return !linksSelection
                        .filter(link => (link.source.id === d.id || link.target.id === d.id))
                        .data()
                        .some(link => link.source.id === node.id || link.target.id === node.id);
                })
                .style("opacity", 0.2);
        }

        const onMouseOut = (event, d) => {
            hoveredNodeIdRef.current = null

            // Restore normal link styling
            linksSelection
                .attr("stroke", "black")
                .attr("stroke-width", 1)
                .style("opacity", 1);

            // Restore normal node styling
            nodesSelection.style("opacity", 1);
        }

        nodesSelection
            .on("mouseover", onMouseOver)
            .on("mouseout", onMouseOut)

        simulationRef.current.on("tick", () => {
            linksSelection
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y)

            nodesSelection.attr("transform", (d) => {
                // Center the 110px wide node on its position
                const nodeWidth = 110;
                const nodeHeight = 60; // Approximate height
                return `translate(${d.x - nodeWidth / 2}, ${d.y - nodeHeight / 2})`;
            });
        })

        nodesSelection.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))

        // Reduce initial alpha to make movement smoother
        simulationRef.current.alpha(0.3).restart();
    }, [dataset, height, width, expandedNodes, clusterSpecialTypes, centerStrength, clusterStrength, moduleRadialStrength, linkDistance, linkStrength, nodeRepulsion, collisionRadius])

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
                <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
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
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <input
                            id="clusterToggle"
                            type="checkbox"
                            checked={clusterSpecialTypes}
                            onChange={(e) => setClusterSpecialTypes(e.target.checked)}
                        />
                        <label htmlFor="clusterToggle">Cluster Handlers/SQL</label>
                    </div>

                    {/* Force Parameter Sliders */}
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                        <label>Link Distance:</label>
                        <input
                            type="range"
                            min="50"
                            max="800"
                            value={linkDistance}
                            onChange={(e) => setLinkDistance(Number(e.target.value))}
                        />
                        <span>{linkDistance}</span>

                        <label>Link Strength:</label>
                        <input
                            type="range"
                            min="0.1"
                            max="2"
                            step="0.1"
                            value={linkStrength}
                            onChange={(e) => setLinkStrength(Number(e.target.value))}
                        />
                        <span>{linkStrength.toFixed(1)}</span>

                        <label>Node Repulsion:</label>
                        <input
                            type="range"
                            min="-50"
                            max="0"
                            value={nodeRepulsion}
                            onChange={(e) => setNodeRepulsion(Number(e.target.value))}
                        />
                        <span>{nodeRepulsion}</span>

                        <label>Collision Radius:</label>
                        <input
                            type="range"
                            min="10"
                            max="200"
                            value={collisionRadius}
                            onChange={(e) => setCollisionRadius(Number(e.target.value))}
                        />
                        <span>{collisionRadius}</span>

                        <label>Cluster Strength:</label>
                        <input
                            type="range"
                            min="0"
                            max="0.5"
                            step="0.01"
                            value={clusterStrength}
                            onChange={(e) => setClusterStrength(Number(e.target.value))}
                        />
                        <span>{clusterStrength.toFixed(2)}</span>

                        <label>Module Radial:</label>
                        <input
                            type="range"
                            min="0"
                            max="0.5"
                            step="0.01"
                            value={moduleRadialStrength}
                            onChange={(e) => setModuleRadialStrength(Number(e.target.value))}
                        />
                        <span>{moduleRadialStrength.toFixed(2)}</span>

                        <label>Center Strength:</label>
                        <input
                            type="range"
                            min="0"
                            max="0.1"
                            step="0.01"
                            value={centerStrength}
                            onChange={(e) => setCenterStrength(Number(e.target.value))}
                        />
                        <span>{centerStrength.toFixed(2)}</span>
                    </div>

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