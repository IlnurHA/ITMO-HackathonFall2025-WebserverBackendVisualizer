import React, { useState, useEffect } from 'react';

const CFGVisualizer = () => {
  const [jsonData, setJsonData] = useState(null);
  const [repoPath, setRepoPath] = useState('');
  const [includeTests, setIncludeTests] = useState(false);
  const [mode, setMode] = useState('overview');
  const [selectedFunction, setSelectedFunction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingStats, setProcessingStats] = useState(null);
  
  useEffect(() => {
    if (!jsonData) return;
    
    setIsLoading(true);
    const startTime = performance.now();
    
    try {
      setTimeout(() => {
        if (mode === 'overview') {
        } else if (mode === 'cfg' && selectedFunction) {
        }
        
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        setProcessingStats({ 
          duration
        });
        
      }, 100);
    } catch (err) {
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      setError(`Ошибка при обработке данных за ${duration}мс: ${err.message}`);
      console.error('Ошибка обработки данных:', err);
    } finally {
      setIsLoading(false);
    }
  }, [mode, selectedFunction, jsonData]);

  const handleNodeClick = (node) => {
    if (!node) return;
    
    if (mode === 'overview' && node.type === 'function') {
      setSelectedFunction(node);
      setMode('cfg');
    }
  };

  const handleBack = () => {
    setMode('overview');
    setSelectedFunction(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch("http://localhost:8000/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_root: repoPath,
          include_tests: includeTests,
          max_depth: 10 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server returned status ${response.status}`);
      }

      const result = await response.json();
      setJsonData(result.dependencies);
      setError(null);
    } catch (err) {
      setError(`Ошибка при запросе к серверу: ${err.message}`);
      console.error("Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setJsonData(null);
    setError(null);
    setProcessingStats(null);
    setMode('overview');
    setSelectedFunction(null);
    setRepoPath('');
  };

  const renderTextGraph = () => {
    if (!jsonData) return null;

    if (mode === 'overview') {
      if (!jsonData.modules || jsonData.modules.length === 0) {
        return (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <p>Нет данных для отображения</p>
          </div>
        );
      }
      
      return (
        <div className="modules-container">
          <h3 className="section-title">Структура проекта</h3>
          {jsonData.modules.map((module, index) => {
            const fileName = module.module.split('/').pop().split('\\').pop();
            return (
              <div key={index} className="module-card">
                <div 
                  className="module-header"
                  onClick={() => handleNodeClick({
                    label: fileName,
                    fullLabel: module.module,
                    type: 'module'
                  })}
                >
                  <span className="folder-icon">📁</span>
                  <span className="module-name">{fileName}</span>
                  <span className="module-path">{module.module}</span>
                </div>
                
                {module.tree?.children && module.tree.children.length > 0 ? (
                  <div className="functions-container">
                    <div className="functions-header">
                      Функции ({module.tree.children.length}):
                    </div>
                    <div className="functions-grid">
                      {module.tree.children.map((func, funcIndex) => {
                        const displayName = func.name.length > 30 
                          ? `${func.name.substring(0, 27)}...` 
                          : func.name;
                        
                        return (
                          <div 
                            key={funcIndex}
                            className={`function-item ${func.cfg ? '' : 'no-cfg'}`}
                            onClick={(e) => handleNodeClick({
                              label: func.name,
                              type: 'function',
                              cfg: func.cfg,
                              module: module.module,
                              fileName: fileName
                            }, e)}
                            title={func.name}
                          >
                            <span className="function-icon">●</span> 
                            <span className="function-name">{displayName}</span>
                            {!func.cfg && <span className="no-cfg-badge">(без CFG)</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="no-functions">
                    Нет функций для отображения
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    } else if (mode === 'cfg' && selectedFunction) {
      if (!selectedFunction.cfg || !selectedFunction.cfg.nodes || selectedFunction.cfg.nodes.length === 0) {
        return (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <p>Нет данных CFG для отображения</p>
            <button onClick={handleBack} className="back-button">Вернуться к обзору</button>
          </div>
        );
      }
      
      return (
        <div className="cfg-container">
          <div className="cfg-header">
            <h3 className="cfg-title">
              CFG для функции: <span className="function-name" title={selectedFunction.label}>{selectedFunction.label}</span> в <span className="module-name">{selectedFunction.fileName}</span>
            </h3>
            <button onClick={handleBack} className="back-button">
              ← Вернуться к обзору
            </button>
          </div>
          
          <div className="cfg-nodes-container">
            {selectedFunction.cfg.nodes.map((node, index) => {
              const displayLabel = node.label && node.label.length > 40 
                ? `${node.label.substring(0, 37)}...` 
                : node.label || 'Без названия';
              
              return (
                <div 
                  key={index} 
                  className={`cfg-node ${node.ast_type?.toLowerCase() || 'default'} ${selectedFunction.cfg.entry_node_id?.toString() === node.id.toString() ? 'entry-node' : ''} ${selectedFunction.cfg.exit_node_id?.toString() === node.id.toString() ? 'exit-node' : ''}`}
                  title={node.label}
                >
                  <div className="node-header">
                    <span className="node-id">ID: {node.id}</span>
                    {selectedFunction.cfg.entry_node_id?.toString() === node.id.toString() && (
                      <span className="node-badge entry-badge">ENTRY</span>
                    )}
                    {selectedFunction.cfg.exit_node_id?.toString() === node.id.toString() && (
                      <span className="node-badge exit-badge">EXIT</span>
                    )}
                    {node.ast_type && (
                      <span className="node-badge ast-badge">{node.ast_type}</span>
                    )}
                  </div>
                  
                  <div className="node-label" title={node.label}>
                    {displayLabel}
                  </div>
                  
                  {(node.successors && node.successors.length > 0) && (
                    <div className="node-links">
                      <strong>Successors:</strong>
                      <div className="links-list">
                        {node.successors.map((targetId, i) => (
                          <span key={i} className="link-item">{targetId}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {(node.predecessors && node.predecessors.length > 0) && (
                    <div className="node-links">
                      <strong>Predecessors:</strong>
                      <div className="links-list">
                        {node.predecessors.map((sourceId, i) => (
                          <span key={i} className="link-item">{sourceId}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    
    return null;
  };

  return (
    <div className="visualizer-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>CFG Visualizer</h1>
          <div className="header-subtitle">
            {mode === 'overview' ? 'Обзор проекта' : `CFG для функции: ${selectedFunction?.label}`}
          </div>
        </div>
      </header>
      
      {/* Path Input Form (показываем только если нет данных) */}
      {!jsonData && (
        <div className="path-input-container">
          <h2>Анализ зависимостей проекта</h2>
          <form onSubmit={handleSubmit} className="path-form">
            <div className="form-group">
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
            </div>
            
            <div className="form-group checkbox-group">
              <input
                id="includeTests"
                type="checkbox"
                checked={includeTests}
                onChange={(e) => setIncludeTests(e.target.checked)}
              />
              <label htmlFor="includeTests">Включить тестовые зависимости</label>
            </div>
            
            <button 
              type="submit" 
              disabled={isLoading}
              className="analyze-button"
            >
              {isLoading ? 'Анализирую...' : 'Анализировать проект'}
            </button>
          </form>
          
          {error && (
            <div className="error-container">
              <div className="error-icon">❌</div>
              <div className="error-message">{error}</div>
            </div>
          )}
        </div>
      )}
      
      {/* File Info & Controls (показываем только если есть данные) */}
      {jsonData && (
        <div className="controls-container">
          <div className="file-info">
            <div className="file-name">🔍 Анализ для: {repoPath}</div>
            {processingStats && (
              <div className="stats">
                <span>Обработано за: {processingStats.duration}мс</span>
              </div>
            )}
          </div>
          
          <div className="header-actions">
            <button onClick={handleReset} className="reset-button">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 19l-7-7 7-7" />
              </svg>
              Новый анализ
            </button>
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <main className="main-content">
        {isLoading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <div>Загрузка и обработка данных...</div>
          </div>
        )}
        
        {error && !isLoading && (
          <div className="error-container">
            <div className="error-icon">❌</div>
            <div className="error-message">{error}</div>
          </div>
        )}
        
        {!isLoading && renderTextGraph()}
      </main>
      
      {/* CSS стили */}
      <style jsx>{`
        .visualizer-container {
          width: 100%;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background-color: #1a1a25;
          color: #e0e6ff;
          font-family: 'Arial', sans-serif;
          overflow-x: hidden;
        }
        
        .app-header {
          background-color: rgba(10, 12, 20, 0.9);
          padding: 15px 20px;
          border-bottom: 1px solid #3a4266;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-shrink: 0;
        }
        
        .header-content h1 {
          margin: 0;
          font-size: 24px;
          background: linear-gradient(90deg, #6a5acd, #5d73e5);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          font-weight: bold;
        }
        
        .header-subtitle {
          color: #b4c8e6;
          font-size: 14px;
          margin-top: 3px;
        }
        
        .path-input-container {
          padding: 40px 20px;
          text-align: center;
          max-width: 800px;
          margin: 0 auto;
          width: 100%;
        }
        
        .path-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
          margin-top: 20px;
        }
        
        .form-group {
          text-align: left;
        }
        
        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: bold;
          text-align: left;
        }
        
        .path-input {
          width: 100%;
          padding: 12px;
          border: 1px solid #5d73e5;
          border-radius: 6px;
          background-color: #2a2d3c;
          color: white;
          font-size: 16px;
        }
        
        .checkbox-group {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .checkbox-group label {
          margin-bottom: 0;
          cursor: pointer;
        }
        
        .analyze-button {
          padding: 12px 24px;
          background-color: #5d73e5;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 16px;
          font-weight: bold;
          cursor: pointer;
          transition: background-color 0.3s;
          align-self: flex-start;
        }
        
        .analyze-button:hover {
          background-color: #4d63d5;
        }
        
        .analyze-button:disabled {
          background-color: #6a7be5;
          cursor: not-allowed;
        }
        
        .controls-container {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 10px 20px;
          background-color: rgba(10, 12, 20, 0.9);
          border-bottom: 1px solid #3a4266;
        }
        
        .file-info {
          display: flex;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 15px;
          align-items: center;
        }
        
        .file-name {
          font-weight: bold;
          color: #8ab4d6;
          font-size: 16px;
        }
        
        .header-actions {
          display: flex;
          gap: 10px;
          margin-left: auto;
        }
        
        .reset-button {
          padding: 8px 16px;
          background-color: rgba(220, 50, 50, 0.2);
          border: 1px solid #dc3232;
          color: white;
          border-radius: 20px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s;
        }
        
        .reset-button:hover {
          background-color: rgba(220, 50, 50, 0.3);
        }
        
        .stats {
          display: flex;
          gap: 15px;
          color: #b4c8e6;
          font-size: 13px;
        }
        
        .main-content {
          flex: 1;
          overflow: auto;
          padding: 20px;
        }
        
        .error-container {
          padding: 15px;
          background-color: rgba(255, 85, 85, 0.1);
          border: 1px solid #ff5555;
          border-radius: 8px;
          margin: 15px 0;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .error-icon {
          font-size: 24px;
          color: #ff6a6a;
        }
        
        .error-message {
          color: #ffcccc;
        }
        
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px;
          color: #8ab4d6;
        }
        
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(93, 115, 229, 0.3);
          border-top: 4px solid #5d73e5;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 15px;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .modules-container {
          padding: 10px;
        }
        
        .section-title {
          color: #5d73e5;
          margin-bottom: 15px;
          font-size: 20px;
        }
        
        .module-card {
          margin-bottom: 20px;
          border-left: 3px solid #6a5acd;
          padding-left: 15px;
          border-bottom: 1px solid #3a4266;
          padding-bottom: 15px;
        }
        
        .module-header {
          font-size: 18px;
          font-weight: bold;
          color: #8aa0e5;
          cursor: pointer;
          padding: 8px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        
        .module-header:hover {
          background-color: rgba(106, 90, 205, 0.1);
        }
        
        .folder-icon {
          font-size: 16px;
        }
        
        .module-name {
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 300px;
          white-space: nowrap;
        }
        
        .module-path {
          font-size: 14px;
          color: #7a88b6;
          margin-left: 10px;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 400px;
          white-space: nowrap;
          display: inline-block;
        }
        
        .functions-container {
          margin-left: 20px;
          margin-top: 10px;
        }
        
        .functions-header {
          font-weight: bold;
          color: #6aa7b4;
          margin-bottom: 8px;
          font-size: 16px;
        }
        
        .functions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 10px;
        }
        
        .function-item {
          padding: 10px;
          border: 1px solid #4682b4;
          border-radius: 6px;
          background-color: rgba(70, 130, 180, 0.08);
          cursor: pointer;
          transition: all 0.2s;
          color: #e6f0ff;
          display: flex;
          align-items: center;
          gap: 8px;
          overflow: hidden;
        }
        
        .function-item:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
          background-color: rgba(93, 115, 229, 0.15);
        }
        
        .function-item.no-cfg {
          border: 1px dashed #777;
          background-color: rgba(100, 100, 100, 0.1);
          color: #aaa;
        }
        
        .function-icon {
          color: #8ab4d6;
          font-weight: bold;
        }
        
        .function-name {
          display: inline-block;
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .no-cfg-badge {
          font-size: 12px;
          margin-left: 5px;
          color: #ffaa33;
          white-space: nowrap;
        }
        
        .no-functions {
          margin-left: 20px;
          color: #aaa;
          font-style: italic;
        }
        
        .cfg-container {
          display: flex;
          flex-direction: column;
          height: 100%;
        }
        
        .cfg-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          margin-bottom: 15px;
          padding-bottom: 10px;
          border-bottom: 1px solid #3a4266;
        }
        
        .cfg-title {
          color: #5d73e5;
          margin: 0;
          font-size: 20px;
          max-width: 100%;
        }
        
        .function-name {
          color: #8ab4d6;
        }
        
        .module-name {
          color: #a690cc;
        }
        
        .back-button {
          padding: 6px 12px;
          background-color: #5d73e5;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 5px;
          transition: background-color 0.3s;
          white-space: nowrap;
        }
        
        .back-button:hover {
          background-color: #4d63d5;
        }
        
        .cfg-nodes-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 15px;
          padding-right: 10px;
        }
        
        .cfg-node {
          padding: 14px;
          border: 1px solid #3a4266;
          border-radius: 6px;
          background-color: #2a2d3c;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .cfg-node:hover {
          background-color: #323648;
          border-color: #5d73e5;
        }
        
        .cfg-node.entry-node {
          border-left: 4px solid #6cd785;
        }
        
        .cfg-node.exit-node {
          border-left: 4px solid #ff8a8a;
        }
        
        .node-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
          flex-wrap: wrap;
          gap: 5px;
        }
        
        .node-id {
          font-size: 14px;
          font-weight: bold;
          color: #8ab4d6;
          background-color: #3a4266;
          padding: 2px 6px;
          border-radius: 4px;
          white-space: nowrap;
        }
        
        .node-badge {
          font-size: 12px;
          font-weight: bold;
          padding: 2px 6px;
          border-radius: 4px;
          margin-left: 8px;
          white-space: nowrap;
        }
        
        .entry-badge {
          color: #6cd785;
          background-color: rgba(108, 215, 133, 0.15);
          border: 1px solid rgba(108, 215, 133, 0.3);
        }
        
        .exit-badge {
          color: #ff8a8a;
          background-color: rgba(255, 138, 138, 0.15);
          border: 1px solid rgba(255, 138, 138, 0.3);
        }
        
        .ast-badge {
          color: #a8b2cc;
          background-color: #3a4266;
        }
        
        .node-label {
          font-size: 16px;
          font-weight: 500;
          color: #e0e6ff;
          line-height: 1.4;
          margin-bottom: 10px;
          padding: 8px;
          background-color: #323648;
          border-radius: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          max-height: 60px;
        }
        
        .node-links {
          margin-top: 8px;
          font-size: 14px;
          color: #8ab4d6;
        }
        
        .links-list {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 4px;
        }
        
        .link-item {
          font-size: 13px;
          color: #b4c8e6;
          background-color: #3a4266;
          padding: 2px 8px;
          border-radius: 12px;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 80px;
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: calc(100% - 80px);
          text-align: center;
          padding: 40px;
        }
        
        .empty-icon {
          font-size: 48px;
          margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
          .functions-grid {
            grid-template-columns: 1fr;
          }
          
          .cfg-nodes-container {
            grid-template-columns: 1fr;
          }
          
          .controls-container {
            flex-direction: column;
            align-items: flex-start;
          }
          
          .header-actions {
            width: 100%;
            margin-left: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default CFGVisualizer;