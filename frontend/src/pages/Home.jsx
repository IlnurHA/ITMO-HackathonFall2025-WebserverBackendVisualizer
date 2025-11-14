import { useState, useEffect, useRef } from "react";

const Home = () => {
  const [repoPath, setRepoPath] = useState("");
  const [includeTests, setIncludeTests] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const resultsRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch("http://localhost:8000/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_root: repoPath,
          include_tests: includeTests,
          max_depth: 10 // Используем фиксированное значение глубины
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server returned status ${response.status}`);
      }

      const result = await response.json();

      //ТУТА ЗАБИРАЕМ ДАННЫЕ С БЭКА
      setData(result.dependencies);


    } catch (err) {
      setError(err.message || "Failed to fetch data from server");
      console.error("Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Автоматическая прокрутка к результатам при их загрузке
  useEffect(() => {
    if (data && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [data]);

  return (
    <div style={{
      padding: "2rem",
      maxWidth: "900px",
      margin: "0 auto",
      fontFamily: "Arial, sans-serif",
      minHeight: "100vh" // Гарантируем, что контейнер будет занимать всю высоту
    }}>
      <h1 style={{ color: "#333" }}>Dependency Visualizer</h1>
      <p>Enter your project path to analyze dependencies</p>

      <form onSubmit={handleSubmit} style={{
        marginBottom: "2rem",
        padding: "1.5rem",
        border: "1px solid #ddd",
        borderRadius: "8px",
        backgroundColor: "#f9f9f9"
      }}>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="repoPath" style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
            Repository Path:
          </label>
          <input
            id="repoPath"
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="/path/to/your/project (required)"
            style={{
              width: "100%",
              padding: "0.75rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "1rem"
            }}
            required
          />
          <small style={{ color: "#666", display: "block", marginTop: "0.25rem" }}>
            Example: /Users/username/project or C:\\Users\\username\\project
          </small>
        </div>

        <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center" }}>
          <input
            id="includeTests"
            type="checkbox"
            checked={includeTests}
            onChange={(e) => setIncludeTests(e.target.checked)}
            style={{ marginRight: "0.5rem" }}
          />
          <label htmlFor="includeTests" style={{ fontSize: "0.95rem" }}>
            Include test dependencies in analysis
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          style={{
            padding: "0.85rem 1.75rem",
            backgroundColor: isLoading ? "#a0a0a0" : "#0066cc",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: isLoading ? "not-allowed" : "pointer",
            fontSize: "1rem",
            fontWeight: "bold",
            transition: "background-color 0.2s"
          }}
          onMouseOver={(e) => !isLoading && (e.target.style.backgroundColor = "#0055aa")}
          onMouseOut={(e) => !isLoading && (e.target.style.backgroundColor = "#0066cc")}
        >
          {isLoading ? "Analyzing..." : "Analyze Dependencies"}
        </button>
      </form>

      {error && (
        <div style={{
          padding: "1rem",
          backgroundColor: "#fff1f1",
          border: "1px solid #ff9999",
          borderRadius: "4px",
          color: "#cc0000",
          marginBottom: "1.5rem"
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {isLoading && (
        <div style={{
          padding: "1rem",
          backgroundColor: "#e6f7ff",
          border: "1px solid #91d5ff",
          borderRadius: "4px",
          marginBottom: "1.5rem"
        }}>
          Analyzing dependencies, please wait...
        </div>
      )}

      {data && (
        <div ref={resultsRef} style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          overflow: "hidden",
          marginBottom: "2rem"
        }}>
          <div style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#f5f5f5",
            fontWeight: "bold",
            borderBottom: "1px solid #ddd"
          }}>
            Analysis Results
          </div>
          <div style={{
            padding: "1rem",
            maxHeight: "70vh", // Ограничиваем высоту контейнера
            overflowY: "auto", // Добавляем вертикальную прокрутку внутри контейнера
            backgroundColor: "#fcfcfc"
          }}>
            <pre style={{
              margin: 0,
              fontFamily: "Consolas, monospace",
              fontSize: "0.95rem"
            }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div style={{ marginTop: "2rem", padding: "1rem", backgroundColor: "#f8f9fa", borderRadius: "8px", fontSize: "0.9rem" }}>
        <p><strong>Tip:</strong> If you're experiencing connection issues:</p>
        <ul style={{ paddingLeft: "1.5rem", marginTop: "0.5rem" }}>
          <li>Make sure the backend server is running on port 8000</li>
          <li>Check that your repository path exists and is accessible</li>
          <li>Install React DevTools browser extension for better debugging: <a href="https://react.dev/link/react-devtools" target="_blank" rel="noopener noreferrer" style={{ color: "#0066cc" }}>https://react.dev/link/react-devtools</a></li>
        </ul>
      </div>

      {/* Пустой div для отступа внизу, чтобы результаты были видны при прокрутке */}
      <div style={{ height: "2rem" }}></div>
    </div>
  );
};

export default Home;
