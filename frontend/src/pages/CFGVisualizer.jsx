import React, { useState, useRef, useEffect, useMemo } from 'react';

// Error Boundary компонент, определенный внутри этого файла
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#2a2a2a', 
          border: '1px solid #ff4444', 
          borderRadius: '8px',
          color: '#ff5555',
          height: '100%',
          overflow: 'auto'
        }}>
          <h2>Ошибка при визуализации графа</h2>
          <details style={{ whiteSpace: 'pre-wrap', color: '#aaa', marginBottom: '15px' }}>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo?.componentStack}
          </details>
          <p>Причина может быть в:</p>
          <ul style={{ textAlign: 'left', paddingLeft: '20px' }}>
            <li>Проблемы с версиями React и зависимостей</li>
            <li>Слишком большой объем данных для визуализации</li>
            <li>Некорректная структура CFG данных</li>
          </ul>
          <button 
            onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
            style={{ 
              marginTop: '15px', 
              padding: '10px 20px', 
              backgroundColor: '#4a90e2', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Попробовать снова
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const CFGVisualizer = () => {
  // Состояния компонента
  const [jsonData, setJsonData] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [mode, setMode] = useState('overview');
  const [viewMode, setViewMode] = useState('text'); // 'graph' или 'text' по умолчанию 'text'
  const [selectedFunction, setSelectedFunction] = useState(null);
  const [hoverNode, setHoverNode] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [processingStats, setProcessingStats] = useState(null);
  const fileInputRef = useRef(null);
  const containerRef = useRef(null);
  
  // Для графической визуализации
  const [isGraphAvailable, setIsGraphAvailable] = useState(false);
  const [graphError, setGraphError] = useState(null);
  const FG2D = useRef(null);

  useEffect(() => {
    // Динамический импорт ForceGraph2D для избежания проблем с SSR и хуками
    let isMounted = true;
    
    const loadGraphLibrary = async () => {
      try {
        const module = await import('react-force-graph-2d');
        if (isMounted) {
          FG2D.current = module.default;
          setIsGraphAvailable(true);
          setGraphError(null);
        }
      } catch (err) {
        console.error('Ошибка при загрузке ForceGraph2D:', err);
        if (isMounted) {
          setGraphError('Не удалось загрузить библиотеку визуализации графов. Будет использован текстовый режим.');
        }
      }
    };
    
    loadGraphLibrary();
    
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!jsonData) return;
    
    setIsLoading(true);
    const startTime = performance.now();
    
    try {
      setTimeout(() => {
        if (mode === 'overview') {
          buildOverviewGraph();
        } else if (mode === 'cfg' && selectedFunction) {
          buildCFGGraph();
        }
        
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        setProcessingStats({ 
          duration, 
          nodeCount: graphData.nodes.length, 
          linkCount: graphData.links.length 
        });
        
      }, 100);
    } catch (err) {
      const endTime = performance.now();
      const duration = (endTime - startTime).toFixed(2);
      setError(`Ошибка при построении графа за ${duration}мс: ${err.message}`);
      console.error('Ошибка построения графа:', err);
    } finally {
      setIsLoading(false);
    }
  }, [mode, selectedFunction, jsonData]);

  const buildOverviewGraph = () => {
    if (!jsonData?.modules) {
      setGraphData({ nodes: [], links: [] });
      return;
    }

    const nodes = [];
    const links = [];
    let moduleCount = 0;
    let functionCount = 0;

    jsonData.modules.forEach((module, index) => {
      if (!module.module) return;
      
      const moduleId = `module_${index}`;
      const fileName = module.module.split('/').pop();
      
      nodes.push({
        id: moduleId,
        label: fileName,
        fullLabel: module.module,
        type: 'module',
        size: 15,
        val: 15,
        moduleData: module
      });
      
      moduleCount++;
      
      if (module.tree?.children) {
        module.tree.children.forEach((func, funcIndex) => {
          if (!func.name || !func.cfg) return;
          
          const funcId = `${moduleId}_func_${funcIndex}`;
          nodes.push({
            id: funcId,
            label: func.name,
            fullLabel: `${module.module}::${func.name}`,
            type: 'function',
            module: moduleId,
            fileName: fileName,
            cfg: func.cfg,
            functionData: func,
            size: 10,
            val: 10
          });
          
          links.push({
            source: moduleId,
            target: funcId,
            type: 'contains'
          });
          
          functionCount++;
        });
      }
    });

    setGraphData({ nodes, links });
    console.log(`Обзорный граф построен: ${moduleCount} модулей, ${functionCount} функций`);
  };

  const buildCFGGraph = () => {
    if (!selectedFunction || !selectedFunction.cfg) {
      setMode('overview');
      return;
    }

    const cfg = selectedFunction.cfg;
    const nodes = [];
    const links = [];
    
    if (!cfg.nodes || !Array.isArray(cfg.nodes)) {
      setError('Некорректная структура CFG: отсутствуют ноды');
      setMode('overview');
      return;
    }

    cfg.nodes.forEach(node => {
      if (node.id === undefined) return;
      
      const nodeId = `cfg_${node.id}`;
      const isEntry = cfg.entry_node_id?.toString() === node.id.toString();
      const isExit = cfg.exit_node_id?.toString() === node.id.toString();
      
      nodes.push({
        id: nodeId,
        label: node.label?.length > 20 ? `${node.label.substring(0, 17)}...` : node.label || `Node ${node.id}`,
        fullLabel: node.label || `Node ${node.id}`,
        type: 'cfg_node',
        ast_type: node.ast_type,
        isEntry,
        isExit,
        size: isEntry || isExit ? 12 : 8,
        val: isEntry || isExit ? 12 : 8,
        originalNode: node
      });
    });

    cfg.nodes.forEach(node => {
      if (!node.successors) return;
      
      const sourceId = `cfg_${node.id}`;
      
      node.successors.forEach(targetId => {
        if (targetId === undefined) return;
        
        const actualTargetId = `cfg_${targetId}`;
        if (nodes.some(n => n.id === actualTargetId)) {
          links.push({
            source: sourceId,
            target: actualTargetId,
            type: 'cfg_edge'
          });
        }
      });
    });

    setGraphData({ nodes, links });
  };

  const handleNodeClick = (node) => {
    if (!node) return;
    
    if (mode === 'overview' && node.type === 'function') {
      setSelectedFunction(node);
      setMode('cfg');
      setViewMode('text'); // По умолчанию текстовый режим для деталей
    }
  };

  const handleNodeHover = (node, event) => {
    if (node && event) {
      setHoverNode(node);
      setTooltipPosition({ 
        x: event.clientX + 10, 
        y: event.clientY + 10 
      });
    } else {
      setHoverNode(null);
    }
  };

  const getNodeColor = (node) => {
    if (mode === 'overview') {
      if (node.type === 'module') return '#6a5acd';
      if (node.type === 'function') return '#4682b4';
    } else if (mode === 'cfg') {
      if (node.isEntry) return '#32cd32';
      if (node.isExit) return '#ff4500';
      if (node.ast_type === 'FunctionDef') return '#9370db';
      if (node.label.toLowerCase().includes('if')) return '#ff6347';
      if (node.label.toLowerCase().includes('while') || node.label.toLowerCase().includes('for')) return '#ffd700';
      if (node.label.toLowerCase().includes('return')) return '#ff1493';
      if (node.label.toLowerCase().includes('call')) return '#20b2aa';
      return '#87ceeb';
    }
    return '#ccc';
  };

  const getNodeCanvasObject = (node, ctx, globalScale) => {
    const label = node.label || '';
    const fontSize = 12 / globalScale;
    
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI, false);
    ctx.fillStyle = getNodeColor(node);
    
    if (mode === 'cfg' && (node.isEntry || node.isExit)) {
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, node.size * 2
      );
      gradient.addColorStop(0, getNodeColor(node) + 'cc');
      gradient.addColorStop(1, getNodeColor(node) + '00');
      ctx.fillStyle = gradient;
      ctx.fillRect(node.x - node.size * 2, node.y - node.size * 2, node.size * 4, node.size * 4);
    }
    
    ctx.fill();
    ctx.strokeStyle = '#222';
    ctx.lineWidth = 1 / globalScale;
    ctx.stroke();
    
    if (globalScale > 0.5) {
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#fff';
      ctx.font = `${fontSize}px Arial`;
      ctx.fillText(label, node.x, node.y);
    }
  };

  const handleBack = () => {
    setMode('overview');
    setSelectedFunction(null);
    setViewMode('text');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setIsLoading(true);
    setError(null);
    setFileInfo({
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: new Date(file.lastModified)
    });
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target.result);
        setJsonData(json);
        setError(null);
      } catch (err) {
        setError(`Ошибка при парсинге JSON: ${err.message}. Проверьте консоль для деталей.`);
        console.error('Ошибка парсинга JSON:', err);
      } finally {
        setIsLoading(false);
      }
    };
    reader.onerror = () => {
      setError('Ошибка при чтении файла');
      setIsLoading(false);
    };
    reader.readAsText(file);
  };

  const handleReset = () => {
    setJsonData(null);
    setError(null);
    setFileInfo(null);
    setProcessingStats(null);
    setMode('overview');
    setSelectedFunction(null);
    setViewMode('text');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const renderTextGraph = () => {
    if (mode === 'overview') {
      if (!jsonData?.modules || jsonData.modules.length === 0) {
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
          {jsonData.modules.map((module, index) => (
            <div key={index} className="module-card">
              <div 
                className="module-header"
                onClick={() => handleNodeClick({
                  label: module.module.split('/').pop(),
                  fullLabel: module.module,
                  type: 'module'
                })}
              >
                <span className="folder-icon">📁</span>
                <span className="module-name">{module.module}</span>
              </div>
              
              {module.tree?.children && module.tree.children.length > 0 ? (
                <div className="functions-container">
                  <div className="functions-header">
                    Функции ({module.tree.children.length}):
                  </div>
                  <div className="functions-grid">
                    {module.tree.children.map((func, funcIndex) => (
                      <div 
                        key={funcIndex}
                        className={`function-item ${func.cfg ? '' : 'no-cfg'}`}
                        onClick={(e) => handleNodeClick({
                          label: func.name,
                          type: 'function',
                          cfg: func.cfg,
                          module: module.module,
                          fileName: module.module.split('/').pop()
                        }, e)}
                      >
                        <span className="function-icon">●</span> {func.name}
                        {!func.cfg && <span className="no-cfg-badge">(без CFG)</span>}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="no-functions">
                  Нет функций для отображения
                </div>
              )}
            </div>
          ))}
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
              CFG для функции: <span className="function-name">{selectedFunction.label}</span> в <span className="module-name">{selectedFunction.fileName}</span>
            </h3>
            <button onClick={handleBack} className="back-button">
              ← Вернуться к обзору
            </button>
          </div>
          
          <div className="cfg-nodes-container">
            {selectedFunction.cfg.nodes.map((node, index) => (
              <div 
                key={index} 
                className={`cfg-node ${node.ast_type?.toLowerCase() || 'default'} ${selectedFunction.cfg.entry_node_id?.toString() === node.id.toString() ? 'entry-node' : ''} ${selectedFunction.cfg.exit_node_id?.toString() === node.id.toString() ? 'exit-node' : ''}`}
                onMouseEnter={(e) => handleNodeHover({
                  label: node.label,
                  fullLabel: node.label,
                  ast_type: node.ast_type,
                  originalNode: node
                }, e)}
                onMouseLeave={() => setHoverNode(null)}
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
                
                <div className="node-label">
                  {node.label || 'Без названия'}
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
            ))}
          </div>
        </div>
      );
    }
    
    return null;
  };

  const renderGraphVisualization = () => {
    if (!isGraphAvailable || graphError) {
      return (
        <div className="graph-error">
          <div className="error-icon">⚠️</div>
          <p>{graphError || 'Библиотека визуализации графов недоступна'}</p>
          <p>Переключитесь в текстовый режим для просмотра данных</p>
        </div>
      );
    }
    
    if (!FG2D.current) {
      return (
        <div className="loading-graph">
          <div className="spinner"></div>
          <p>Загрузка библиотеки визуализации...</p>
        </div>
      );
    }
    
    const ForceGraph2D = FG2D.current;
    const fgRef = useRef();
    
    return (
      <ErrorBoundary fallback={<div className="graph-error">Ошибка при отображении графа. Переключитесь в текстовый режим.</div>}>
        <div style={{ width: '100%', height: '100%' }}>
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            backgroundColor="#1a1a1a"
            nodeCanvasObject={getNodeCanvasObject}
            nodePointerAreaPaint={(node, paint) => paint(node.x, node.y, node.size * 1.5)}
            linkWidth={1.5}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={0.99}
            linkCurvature={0.2}
            linkCanvasObjectMode={() => 'after'}
            onNodeHover={handleNodeHover}
            onNodeClick={handleNodeClick}
            onBackgroundClick={() => setHoverNode(null)}
            cooldownTime={3000}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.4}
            warmupTicks={100}
            nodeVal="val"
            dagMode={mode === 'cfg' ? 'lr' : null}
          />
        </div>
      </ErrorBoundary>
    );
  };

  if (!jsonData && !error) {
    return (
      <div className="upload-container">
        <h2>CFG Visualizer</h2>
        <p>Загрузите JSON файл с результатами анализа для визуализации</p>
        <div className="dropzone">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            id="file-upload"
          />
          <label htmlFor="file-upload">
            <div className="upload-icon">📁</div>
            <div className="upload-text">
              <div className="upload-title">Выберите файл или перетащите сюда</div>
              <div className="upload-subtitle">Поддерживаются только JSON файлы</div>
            </div>
          </label>
        </div>
        {isLoading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <div>Загрузка и обработка файла...</div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div 
      className="visualizer-container"
      ref={containerRef}
    >
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>CFG Visualizer</h1>
          <div className="header-subtitle">
            {mode === 'overview' ? 'Обзор проекта' : `CFG для функции: ${selectedFunction?.label}`}
          </div>
        </div>
        
        <div className="header-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            id="file-upload-header"
          />
          <label htmlFor="file-upload-header" className="upload-button">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Загрузить другой файл
          </label>
          <button onClick={handleReset} className="reset-button">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 19l-7-7 7-7" />
            </svg>
            Сбросить
          </button>
        </div>
      </header>
      
      {/* File Info */}
      {fileInfo && (
        <div className="file-info">
          <div className="file-name">📄 {fileInfo.name} ({(fileInfo.size / 1024).toFixed(2)} КБ)</div>
          <div className="view-controls">
            <div className="view-mode">
              <span>Режим просмотра:</span>
              <select 
                value={viewMode} 
                onChange={(e) => setViewMode(e.target.value)}
                className="view-select"
              >
                <option value="text">Текст</option>
                <option value="graph" disabled={!isGraphAvailable}>Граф</option>
              </select>
            </div>
            {processingStats && (
              <div className="stats">
                <span>Обработано за: {processingStats.duration}мс</span>
                <span>Нод: {processingStats.nodeCount}</span>
                <span>Связей: {processingStats.linkCount}</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <main className="main-content">
        {error && (
          <div className="error-container">
            <div className="error-icon">❌</div>
            <div className="error-message">{error}</div>
          </div>
        )}
        
        <ErrorBoundary fallback={
          <div className="error-boundary">
            <h3>Ошибка визуализации</h3>
            <p>Произошла ошибка при отображении данных. Попробуйте переключиться в текстовый режим.</p>
          </div>
        }>
          {viewMode === 'graph' ? renderGraphVisualization() : renderTextGraph()}
        </ErrorBoundary>
      </main>
      
      {/* Tooltip */}
      {hoverNode && (
        <div 
          className="tooltip"
          style={{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`
          }}
        >
          <div className="tooltip-header">
            {mode === 'overview' ? (
              hoverNode.type === 'module' ? 'Модуль' : 'Функция'
            ) : (
              'CFG Узел'
            )}
          </div>
          <div className="tooltip-content">
            <strong>{hoverNode.fullLabel || hoverNode.label}</strong>
            {mode === 'cfg' && hoverNode.ast_type && (
              <div className="tooltip-detail">AST Type: {hoverNode.ast_type}</div>
            )}
            {mode === 'overview' && hoverNode.type === 'function' && (
              <div className="tooltip-detail">Модуль: {hoverNode.fileName}</div>
            )}
            {mode === 'cfg' && hoverNode.originalNode && (
              <div className="tooltip-detail">
                ID: {hoverNode.originalNode.id}
                {hoverNode.originalNode.successors?.length > 0 && (
                  <div>Successors: {hoverNode.originalNode.successors.join(', ')}</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* CSS стили */}
      <style jsx>{`
        .visualizer-container {
          width: 100%;
          height: 100vh;
          display: flex;
          flex-direction: column;
          background-color: #1a1a25;
          color: #e0e6ff;
          font-family: 'Arial', sans-serif;
          overflow: hidden;
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
        
        .header-actions {
          display: flex;
          gap: 10px;
        }
        
        .upload-button, .reset-button {
          padding: 8px 16px;
          border-radius: 20px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s;
        }
        
        .upload-button {
          background-color: rgba(93, 115, 229, 0.2);
          border: 1px solid #5d73e5;
          color: white;
        }
        
        .upload-button:hover {
          background-color: rgba(93, 115, 229, 0.3);
        }
        
        .reset-button {
          background-color: rgba(220, 50, 50, 0.2);
          border: 1px solid #dc3232;
          color: white;
        }
        
        .reset-button:hover {
          background-color: rgba(220, 50, 50, 0.3);
        }
        
        .file-info {
          padding: 10px 20px;
          background-color: rgba(93, 115, 229, 0.1);
          border-bottom: 1px solid #5d73e5;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
        }
        
        .file-name {
          font-weight: bold;
          color: #8ab4d6;
        }
        
        .view-controls {
          display: flex;
          gap: 15px;
          align-items: center;
        }
        
        .view-mode {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .view-select {
          padding: 4px 8px;
          background-color: #2a2d3c;
          border: 1px solid #4a90e2;
          color: white;
          border-radius: 4px;
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
          padding: 20px;
          background-color: rgba(255, 85, 85, 0.1);
          border: 1px solid #ff5555;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        
        .error-icon {
          font-size: 24px;
          color: #ff6a6a;
          margin-right: 10px;
        }
        
        .error-message {
          color: #ffcccc;
        }
        
        .upload-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background-color: #1a1a25;
          color: white;
          padding: 20px;
          text-align: center;
        }
        
        .dropzone {
          border: 2px dashed #5d73e5;
          border-radius: 12px;
          padding: 40px;
          margin: 20px;
          width: 80%;
          cursor: pointer;
          background-color: rgba(93, 115, 229, 0.08);
          transition: all 0.3s;
        }
        
        .dropzone:hover {
          border-color: #8ab4d6;
        }
        
        .upload-icon {
          font-size: 48px;
          margin-bottom: 10px;
        }
        
        .upload-title {
          font-size: 18px;
          font-weight: bold;
          margin-bottom: 5px;
        }
        
        .upload-subtitle {
          color: #b4c8e6;
          font-size: 14px;
        }
        
        .loading-container {
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(93, 115, 229, 0.3);
          border-top: 4px solid #5d73e5;
          border-radius: 50%;
          animation: spin 1s linear infinite;
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
        
        .no-cfg-badge {
          font-size: 12px;
          margin-left: 5px;
          color: #ffaa33;
        }
        
        .no-functions {
          margin-left: 20px;
          color: #aaa;
          font-style: italic;
        }
        
        .cfg-container {
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
        }
        
        .back-button:hover {
          background-color: #4d63d5;
        }
        
        .cfg-nodes-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 15px;
          max-height: calc(100vh - 200px);
          overflow-y: auto;
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
        }
        
        .node-badge {
          font-size: 12px;
          font-weight: bold;
          padding: 2px 6px;
          border-radius: 4px;
          margin-left: 8px;
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
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: calc(100% - 80px);
          text-align: center;
        }
        
        .empty-icon {
          font-size: 48px;
          margin-bottom: 20px;
        }
        
        .tooltip {
          position: fixed;
          background: rgba(20, 22, 35, 0.95);
          border: 1px solid #5d73e5;
          border-radius: 8px;
          padding: 12px;
          color: #e0e6ff;
          font-size: 14px;
          pointer-events: none;
          z-index: 100;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
          max-width: 300px;
        }
        
        .tooltip-header {
          color: #8ab4d6;
          font-weight: bold;
          font-size: 15px;
          margin-bottom: 6px;
        }
        
        .tooltip-content {
          line-height: 1.4;
        }
        
        .tooltip-detail {
          color: #b4c8e6;
          margin-top: 4px;
          font-size: 13px;
        }
        
        .graph-error, .loading-graph, .error-boundary {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          text-align: center;
          padding: 20px;
          color: #ffaa33;
        }
        
        .error-icon {
          font-size: 48px;
          margin-bottom: 20px;
        }
      `}</style>
    </div>
  );
};

export default CFGVisualizer;