import { useState } from "react";
import Tree from "react-d3-tree"
import { useCenteredTree } from "./helpers";
import tmpData from "./sample.json"


function transoformData(json) {
    const transformedData = json.modules.map(it => {
        return {
            name: it.module,
            attributes: { ...it, type: "module" },
            children: it.tree.children.map((module) => {
                if (module.type == "function") {
                    return {
                        name: module.name,
                        attributes: module,
                        children: module.calls.map((func) => {
                            return { name: func.function }
                        })
                    }
                }
                return {
                    name: module.name,
                    attributes: module,
                    children: module.children
                }
            }
            )
        }
    })
    return {
        name: "root",
        children: transformedData
    }
}

const rendeNode = (
    {
        nodeDatum,
        toggleNode,
        foreignObjectProps
    }
) => (
    <foreignObject {...foreignObjectProps} onClick={() => {
        // TODO change to expanding and replace toggle with button?
        toggleNode()
    }
    } style={{
        background: nodeDatum.children && nodeDatum.children?.length != 0 ? "#ffffff" : "#a0a0a0",
        border: "2px solid #2F80ED",
        textAlign: "center",
        boxShadow: "0px 10px 10px rgba(0, 0, 0, 0.1)",
        padding: "5px 0",
        borderRadius: "5px",
    }}>
        <h3>{nodeDatum.name}</h3>
        {nodeDatum.attributes?.type}
    </foreignObject>
)


const TreePage = () => {
    const [dataset, setDataset] = useState(transoformData(tmpData))

    const handleFileChange = (event) => {
        const file = event.target.files[0];

        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const data = JSON.parse(content);

                    setDataset(transoformData(data));
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                }
            };
            reader.readAsText(file);
        }
    };

    const [dimensions, translate, containerRef] = useCenteredTree();



    const foreignObjectProps = { width: 400, height: 100, x: -200, y: -50 };
    const nodeSize = { x: foreignObjectProps.width + 40, y: foreignObjectProps.height + 40 };

    return <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
        <h1>Сюда файл можно</h1>
        <input type="file" accept=".json" onChange={handleFileChange} />
        <h1>Деревяха</h1>
        <div style={{ height: "100%", width: "100%" }} ref={containerRef} >
            {dataset &&
                <Tree
                    data={dataset}
                    pathFunc={"step"}

                    dimensions={dimensions}
                    translate={translate}
                    nodeSize={nodeSize}

                    renderCustomNodeElement={(rd3tProps) => rendeNode({ ...rd3tProps, foreignObjectProps })}

                    initialDepth={1}
                // orientation="vertical"
                />
            }
        </div>
    </div >
}

export default TreePage