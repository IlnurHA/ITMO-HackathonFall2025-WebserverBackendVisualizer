import { useState } from "react";
import Tree from "react-d3-tree"

const tmpData = {
    "modules": [
        {
            "module": "app/utils.py",
            "tree": {
                "children": [
                    {
                        "name": "EmailData",
                        "type": "class",
                        "lineno": 20,
                        "children": [],
                        "calls": [],
                        "decorators": [
                            "dataclass"
                        ]
                    },
                    {
                        "name": "render_email_template",
                        "type": "function",
                        "lineno": 25,
                        "children": [],
                        "args": [],
                        "calls": []
                    },
                    {
                        "name": "send_email",
                        "type": "function",
                        "lineno": 33,
                        "children": [],
                        "args": [],
                        "calls": []
                    },
                    {
                        "name": "generate_test_email",
                        "type": "function",
                        "lineno": 58,
                        "children": [],
                        "args": [
                            "email_to"
                        ],
                        "calls": [
                            {
                                "function": "render_email_template",
                                "module": null,
                                "lineno": 61,
                                "type": "local"
                            },
                            {
                                "function": "EmailData",
                                "module": null,
                                "lineno": 65,
                                "type": "local"
                            }
                        ]
                    },
                    {
                        "name": "generate_reset_password_email",
                        "type": "function",
                        "lineno": 68,
                        "children": [],
                        "args": [
                            "email_to",
                            "email",
                            "token"
                        ],
                        "calls": [
                            {
                                "function": "render_email_template",
                                "module": null,
                                "lineno": 72,
                                "type": "local"
                            },
                            {
                                "function": "EmailData",
                                "module": null,
                                "lineno": 82,
                                "type": "local"
                            }
                        ]
                    },
                    {
                        "name": "generate_new_account_email",
                        "type": "function",
                        "lineno": 85,
                        "children": [],
                        "args": [
                            "email_to",
                            "username",
                            "password"
                        ],
                        "calls": [
                            {
                                "function": "render_email_template",
                                "module": null,
                                "lineno": 90,
                                "type": "local"
                            },
                            {
                                "function": "EmailData",
                                "module": null,
                                "lineno": 100,
                                "type": "local"
                            }
                        ]
                    },
                    {
                        "name": "generate_password_reset_token",
                        "type": "function",
                        "lineno": 103,
                        "children": [],
                        "args": [
                            "email"
                        ],
                        "calls": []
                    },
                    {
                        "name": "verify_password_reset_token",
                        "type": "function",
                        "lineno": 116,
                        "children": [],
                        "args": [
                            "token"
                        ],
                        "calls": []
                    }
                ]
            }
        }
    ]
}

function transoformData(json) {
    const transformedData = json.modules.map(it => {
        return {
            name: it.module, children: it.tree.children.map((module) => {
                if (module.type == "function") {
                    return {
                        ...module, children: module.calls.map((func) => {
                            return { name: func.function }
                        })
                    }
                }
                return module
            }
            )
        }
    })
    return {
        name: "root",
        children: transformedData
    }
}

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


    return <div>
        <h1>Сюда файл можно</h1>
        <input type="file" accept=".json" onChange={handleFileChange} />
        <h1>Деревяха</h1>
        <div id="treeWrapper" style={{ height: 1000 }}>
            {dataset &&
                <Tree
                    data={dataset}
                    initialDepth={1}
                    translate={{ x: 100, y: 100 }}
                />
            }
        </div>
    </div>
}

export default TreePage