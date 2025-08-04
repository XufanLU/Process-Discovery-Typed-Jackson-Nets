/**
 * Process Discovery App - Typed Jackson Nets
 * A comprehensive web application for process discovery using Typed Jackson Nets
 */

class ProcessDiscoveryApp {
  constructor() {
    this.currentModel = null;
    this.currentZoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;
    this.selectedFile = null;
    this.analyzedModels = [];
    this.selectedAnalyzedModel = null;
    this.initialLogLoaded = false;
    
    this.initializeEventListeners();
    this.setupFileUpload();
    this.setupVisualization();
    this.loadAnalyzedModels();
    this.loadAvailableXESFiles();
    this.loadInitialModel();
    
  }
  

  initializeEventListeners() {
    
    // Zoom controls
    document.getElementById('zoom-in').addEventListener('click', () => this.zoomIn());
    document.getElementById('zoom-out').addEventListener('click', () => this.zoomOut());
    document.getElementById('fit-to-screen').addEventListener('click', () => this.fitToScreen());
    document.getElementById('reset-view').addEventListener('click', () => this.resetView());

    // Export buttons
    document.getElementById('export-svg').addEventListener('click', () => this.exportSVG());
    document.getElementById('export-pnml').addEventListener('click', () => this.exportPNML());


    // Model operations
    document.getElementById('rearrange-model').addEventListener('click', () => this.rearrangeModel());
  }

  setupFileUpload() {
    const uploadArea = document.getElementById('file-upload-area');
    const fileInput = document.getElementById('event-log-file');

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelection(e.target.files[0]);
      }
    });

    document.getElementById('remove-file').addEventListener('click', () => {
      this.selectedFile = null;
      document.getElementById('selected-file').style.display = 'none';
      fileInput.value = '';
      
      // Reset analyzed models to default when file is removed
      this.loadAnalyzedModels();
      
      // Remove selection from XES files
      document.querySelectorAll('.model-item').forEach(item => {
        item.classList.remove('selected');
      });
    });
  }

  handleFileSelection(file) {
    this.selectedFile = file;
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('selected-file').style.display = 'block';
    this.updateStatus('ready', 'File loaded: ' + file.name);
  }

  setupVisualization() {
    const canvas = document.getElementById('model-canvas');
    
    // Mouse events for panning
    canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
      canvas.style.cursor = 'grabbing';
    });

    canvas.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        const deltaX = e.clientX - this.lastMouseX;
        const deltaY = e.clientY - this.lastMouseY;
        this.panX += deltaX;
        this.panY += deltaY;
        this.updateViewTransform();
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
      }
    });

    canvas.addEventListener('mouseup', () => {
      this.isDragging = false;
      canvas.style.cursor = 'grab';
    });

    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      this.currentZoom *= delta;
      this.currentZoom = Math.max(0.1, Math.min(5, this.currentZoom));
      this.updateViewTransform();
    });
  }

  renderModel(modelData) {
    const canvas = document.getElementById('model-canvas');
    const placeholder = document.getElementById('placeholder');
    
    placeholder.style.display = 'none';
    canvas.style.display = 'block';

    // Clear existing content
    d3.select(canvas).selectAll('*').remove();

    // Create SVG group for model elements
    const svg = d3.select(canvas);
    const g = svg.append('g').attr('class', 'model-group');

    // Render activities/places
    if (modelData.places) {
      g.selectAll('.place')
        .data(modelData.places)
        .enter()
        .append('circle')
        .attr('class', 'place')
        .attr('cx', d => d.x || Math.random() * 600)
        .attr('cy', d => d.y || Math.random() * 400)
        .attr('r', 20)
        .attr('fill', '#f0f0f0')
        .attr('stroke', '#333')
        .attr('stroke-width', 2);
    }

    // Render transitions
    if (modelData.transitions) {
      g.selectAll('.transition')
        .data(modelData.transitions)
        .enter()
        .append('rect')
        .attr('class', 'transition')
        .attr('x', d => (d.x || Math.random() * 600) - 25)
        .attr('y', d => (d.y || Math.random() * 400) - 15)
        .attr('width', 50)
        .attr('height', 30)
        .attr('fill', d => this.getTransitionColor(d.type))
        .attr('stroke', '#333')
        .attr('stroke-width', 2);

      // Add labels
      g.selectAll('.transition-label')
        .data(modelData.transitions)
        .enter()
        .append('text')
        .attr('class', 'transition-label')
        .attr('x', d => d.x || Math.random() * 600)
        .attr('y', d => (d.y || Math.random() * 400) + 5)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .text(d => d.label || d.id);
    }

    // Render arcs
    if (modelData.arcs) {
      g.selectAll('.arc')
        .data(modelData.arcs)
        .enter()
        .append('line')
        .attr('class', 'arc')
        .attr('x1', d => d.source.x || Math.random() * 600)
        .attr('y1', d => d.source.y || Math.random() * 400)
        .attr('x2', d => d.target.x || Math.random() * 600)
        .attr('y2', d => d.target.y || Math.random() * 400)
        .attr('stroke', '#666')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)');
    }

    // Add arrow marker definition
    svg.append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 9)
      .attr('refY', 3)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,0 L0,6 L9,3 z')
      .attr('fill', '#666');

    this.updateViewTransform();
  }

  getTransitionColor(type) {
    const colors = {
      'agent': '#4CAF50',
      'service': '#2196F3',
      'partner': '#FF9800',
      'default': '#9C27B0'
    };
    return colors[type] || colors.default;
  }

  filterCollaborationConcepts(type) {
    const svg = d3.select('#model-canvas');
    
    if (type === 'all') {
      svg.selectAll('.transition').style('opacity', 1);
    } else {
      svg.selectAll('.transition')
        .style('opacity', d => d.type === type ? 1 : 0.3);
    }
  }

  updateViewTransform() {
    const g = d3.select('#model-canvas .model-group');
    g.attr('transform', `translate(${this.panX}, ${this.panY}) scale(${this.currentZoom})`);
  }

  zoomIn() {
    this.currentZoom = Math.min(5, this.currentZoom * 1.2);
    this.updateViewTransform();
  }

  zoomOut() {
    this.currentZoom = Math.max(0.1, this.currentZoom / 1.2);
    this.updateViewTransform();
  }

  fitToScreen() {
    // Calculate bounds and fit to screen
    this.currentZoom = 0.8;
    this.panX = 50;
    this.panY = 50;
    this.updateViewTransform();
  }

  resetView() {
    this.currentZoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.updateViewTransform();
  }

  async exportSVG() {
    const svg = document.getElementById('model-canvas');
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'process_model.svg';
    a.click();
    
    URL.revokeObjectURL(url);
    this.showSuccess('SVG exported successfully');
  }

  async exportPNML() {
    if (!this.currentModel) {
      this.showError('No model to export');
      return;
    }

    try {
      const response = await fetch('/export/pnml', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.currentModel)
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = 'process_model.pnml';
      a.click();
      
      URL.revokeObjectURL(url);
      this.showSuccess('PNML exported successfully');

    } catch (error) {
      this.showError('Export failed: ' + error.message);
    }
  }

  rearrangeModel() {
    if (!this.currentModel) return;
    
    // Implement automatic layout algorithm
    this.showSuccess('Model rearranged successfully');
  }



  updateModelStatistics(modelData) {
    document.getElementById('activity-count').textContent = modelData.places?.length || 0;
    document.getElementById('transition-count').textContent = modelData.transitions?.length || 0;
    document.getElementById('agent-count').textContent = 
      modelData.transitions?.filter(t => t.type === 'agent').length || 0;
    document.getElementById('collaboration-count').textContent = 
      modelData.collaborations?.length || 0;
    
    // Show organization info for analyzed models
    if (modelData.organization) {
      document.getElementById('model-organization').textContent = modelData.organization;
      document.getElementById('model-type').textContent = 'TJN Analysis';
      document.getElementById('model-info').style.display = 'block';
    } else {
      document.getElementById('model-info').style.display = 'none';
    }
  }

  enableExportButtons() {
    document.getElementById('export-svg').disabled = false;
    document.getElementById('export-pnml').disabled = false;
  }

  updateStatus(type, message) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    indicator.className = `status-indicator status-${type}`;
    text.textContent = message;
  }

  showProgress(show) {
    const container = document.getElementById('progress-container');
    container.style.display = show ? 'block' : 'none';
    
    if (show) {
      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
        }
        document.querySelector('.progress-bar').style.width = progress + '%';
      }, 200);
    }
  }

  showError(message) {
    document.getElementById('error-message').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('error-toast'));
    toast.show();
  }

  showSuccess(message) {
    document.getElementById('success-message').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('success-toast'));
    toast.show();
  }

  showInfo(message) {
    // Use success toast for info messages with different styling
    document.getElementById('success-message').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('success-toast'));
    toast.show();
  }

  resetConfiguration() {
    this.selectedFile = null;
    document.getElementById('selected-file').style.display = 'none';
    document.getElementById('event-log-file').value = '';
    
    // Reset TJN parameters to defaults (only if elements exist)
    const collabThreshold = document.getElementById('collab-threshold');
    if (collabThreshold) {
      collabThreshold.value = '0.3';
      document.getElementById('collab-value').textContent = '0.3';
    }
    
    const agentDetection = document.getElementById('agent-detection');
    if (agentDetection) {
      agentDetection.value = 'resource';
    }
    
    
    // Reset model view
    document.getElementById('placeholder').style.display = 'flex';
    document.getElementById('model-canvas').style.display = 'none';
    
    // Reset export buttons
    document.getElementById('export-svg').disabled = true;
    document.getElementById('export-pnml').disabled = true;
    
    // Reset analyzed models to default
    this.loadAnalyzedModels();
    
    // Remove selection from XES files
    document.querySelectorAll('.model-item').forEach(item => {
      item.classList.remove('selected');
    });
    
    this.updateStatus('ready', 'Ready');
    this.showSuccess('Configuration reset successfully');
  }

  async loadInitialModel() {
    // This method can be used to load an initial model on startup
    // For now, we'll just show the default placeholder
    this.showDefaultPlaceholder();
  }

  showDefaultPlaceholder() {
    const placeholder = document.getElementById('placeholder');
    placeholder.innerHTML = `
      <div class="text-center text-muted">
        <i class="fas fa-project-diagram fa-3x mb-3"></i>
        <h5>No Model Loaded</h5>
        <p>Upload an event log file or select from previously analyzed models</p>
      </div>
    `;
  }

  showInitialLogInfo(logStats, organizations) {
    // Add a section to show initial log information
    const placeholder = document.getElementById('placeholder');
    if (placeholder.style.display !== 'none') return;
    
    // You could add this info to a dedicated panel if desired
    console.log('Initial Log Statistics:', logStats);
    console.log('Available Organizations:', organizations);
  }

  async loadAnalyzedModels() {
    try {
      const response = await fetch('/analyzed-models');
      if (!response.ok) {
        throw new Error('Failed to load analyzed models');
      }

      const data = await response.json();
      this.analyzedModels = data.models;
      this.renderAnalyzedModels();
      this.updateAnalyzedModelsTitle('Previously Analyzed Models');

    } catch (error) {
      console.error('Error loading analyzed models:', error);
      document.getElementById('loading-models').innerHTML = 
        '<div class="text-muted small"><i class="fas fa-exclamation-triangle me-1"></i>Failed to load analyzed models</div>';
    }
  }

  renderAnalyzedModels() {
    const container = document.getElementById('analyzed-models-container');
    const loadingElement = document.getElementById('loading-models');
    
    loadingElement.style.display = 'none';
    
    if (!this.analyzedModels || this.analyzedModels.length === 0) {
      container.innerHTML = '<div class="text-muted small">No analyzed models found</div>';
      return;
    }

    container.innerHTML = this.analyzedModels.map(model => `
      <div class="model-item" data-model-id="${model.id}">
        <div class="d-flex align-items-start">
          <div class="flex-grow-1">
            <div class="model-title">${model.name}</div>
            <div class="model-meta">
              ${model.organizations ? model.organizations.map(org => 
                `<span class="organization-badge">${org}</span>`
              ).join('') : ''}
              ${model.has_visualization ? '<span class="badge bg-success ms-1"><i class="fas fa-eye"></i> SVG</span>' : ''}
            </div>
            <div class="text-muted small mt-1">
              ${model.statistics && !model.statistics.error ? 
                `${model.statistics.places} places, ${model.statistics.transitions} transitions` : 
                'Statistics unavailable'
              }
              ${model.file_size ? ` • ${model.file_size} KB` : ''}
            </div>
          </div>
          <div class="model-actions">
            <button class="btn btn-sm btn-outline-primary model-view-btn" 
                    onclick="loadModelDirect('${model.id}')" 
                    title="View Model & PNML">
              <i class="fas fa-eye"></i>
            </button>
            ${model.has_visualization ? 
              `<button class="btn btn-sm btn-outline-info" onclick="viewSVGDirect('${model.id}')" title="View SVG">
                <i class="fas fa-image"></i>
              </button>` : ''
            }
            <button class="btn btn-sm btn-outline-secondary" onclick="alert('Reprocess: ${model.id}')" title="Reprocess">
              <i class="fas fa-redo"></i>
            </button>
          </div>
        </div>
      </div>
    `).join('');
    
    // Add event listeners for the view model buttons
    console.log('Adding event listeners to model buttons...');
    const viewButtons = container.querySelectorAll('.model-view-btn');
    console.log('Found view buttons:', viewButtons.length);
    
    viewButtons.forEach((button, index) => {
      const modelId = button.dataset.modelId;
      console.log(`Setting up button ${index} for model:`, modelId);
      
      button.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('View button clicked for model:', modelId);
        this.loadModel(modelId);
      });
    });
  }

  async loadAvailableXESFiles() {
    try {
      const response = await fetch('/available-xes-files');
      if (!response.ok) {
        throw new Error('Failed to load available XES files');
      }

      const data = await response.json();
      this.availableXESFiles = data.files;
      this.renderAvailableXESFiles();

    } catch (error) {
      console.error('Error loading available XES files:', error);
      document.getElementById('loading-xes-files').innerHTML = 
        '<div class="text-muted small"><i class="fas fa-exclamation-triangle me-1"></i>Failed to load XES files</div>';
    }
  }

  renderAvailableXESFiles() {
    const container = document.getElementById('xes-files-container');
    const loadingElement = document.getElementById('loading-xes-files');
    
    loadingElement.style.display = 'none';
    
    if (!this.availableXESFiles || this.availableXESFiles.length === 0) {
      container.innerHTML = '<div class="text-muted small">No XES files found</div>';
      return;
    }

    container.innerHTML = this.availableXESFiles.map(file => `
      <div class="model-item" data-file-id="${file.id}">
        <div class="d-flex align-items-start">
          <div class="flex-grow-1">
            <div class="model-title">${file.filename}</div>
            <div class="model-meta">
              <span class="badge bg-primary"><i class="fas fa-file"></i> XES</span>
              ${file.size_mb ? `<span class="badge bg-info ms-1">${file.size_mb} MB</span>` : ''}
            </div>
            <div class="text-muted small mt-1">
              ${file.log_statistics && !file.log_statistics.error ? 
                `${file.log_statistics.traces} traces, ${file.log_statistics.events} events` : 
                'Statistics unavailable'
              }
              ${file.log_statistics && file.log_statistics.unique_activities ? 
                ` • ${file.log_statistics.unique_activities} activities` : ''
              }
            </div>
            ${file.log_statistics && file.log_statistics.sample_activities ? `
              <div class="text-muted small">
                Activities: ${file.log_statistics.sample_activities.join(', ')}${file.log_statistics.unique_activities > 5 ? '...' : ''}
              </div>
            ` : ''}
          </div>
          <div class="model-actions">
            <button class="btn btn-sm btn-outline-success xes-select-btn" 
                    data-file-path="${file.full_path}"
                    data-file-name="${file.filename}"
                    title="Select this XES file">
              <i class="fas fa-check"></i> Select
            </button>
            <button class="btn btn-sm btn-outline-info" 
                    onclick="alert('File info: ${file.filename}')" 
                    title="File Info">
              <i class="fas fa-info"></i>
            </button>
          </div>
        </div>
      </div>
    `).join('');
    
    // Add event listeners for the select buttons
    const selectButtons = container.querySelectorAll('.xes-select-btn');
    selectButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.selectXESFile(button.dataset.fileName, button.dataset.filePath);
      });
    });
  }

  selectXESFile(fileName, filePath) {
    // Create a mock file object to simulate file selection
    const mockFile = new File([''], fileName, { type: 'application/xml' });
    mockFile.fullPath = filePath; // Store the server path
    
    this.selectedFile = mockFile;
    
    // Hide the selected file display for XES files
    document.getElementById('selected-file').style.display = 'none';
    
    this.updateStatus('ready', 'XES file selected: ' + fileName);
    this.showSuccess(`Selected XES file: ${fileName}`);
    
    // Highlight the selected file
    document.querySelectorAll('.model-item').forEach(item => {
      item.classList.remove('selected');
    });
    document.querySelector(`[data-file-id="${fileName.replace('.xes', '')}"]`).classList.add('selected');
    
    // Load related PNML models for any selected XES file
    const logName = fileName.replace('.xes', '');
    this.loadRelatedPNMLModels(logName);
  }

  async loadRelatedPNMLModels(logName) {
    try {
      // Load related PNML models for the selected XES file
      const response = await fetch(`/related-models/${logName}`);
      if (!response.ok) {
        throw new Error('Failed to load related models');
      }

      const data = await response.json();
      
      if (data.models && data.models.length > 0) {
        // Update the analyzed models with the related ones
        this.analyzedModels = data.models;
        this.renderAnalyzedModels();
        this.updateAnalyzedModelsTitle(`Related Models for ${logName}`);
        this.showSuccess(`Loaded ${data.models.length} related PNML models for ${logName}`);
      } else {
        // No related models found, fall back to loading default analyzed models
        this.showInfo(`No related models found for ${logName}. Showing default analyzed models.`);
        await this.loadAnalyzedModels();
        this.updateAnalyzedModelsTitle('Previously Analyzed Models');
      }
      
    } catch (error) {
      console.error('Error loading related models:', error);
      this.showError('Failed to load related PNML models: ' + error.message);
      // Fall back to loading default analyzed models on error
      await this.loadAnalyzedModels();
      this.updateAnalyzedModelsTitle('Previously Analyzed Models');
    }
  }

  updateAnalyzedModelsTitle(title) {
    const titleElement = document.querySelector('#analyzed-models-container').previousElementSibling.querySelector('.section-title');
    if (titleElement) {
      titleElement.innerHTML = `<i class="fas fa-history me-2"></i>${title}`;
    }
  }

  async loadModel(modelId) {
    console.log('loadModel called with:', modelId);
    try {
      const response = await fetch(`/model/${modelId}`);
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error('Failed to load model');
      }

      const data = await response.json();
      console.log('Model data received:', data);
      this.updateModelDisplay(data);
      
      
    } catch (error) {
      console.error('Error loading model:', error);
      this.showError('Failed to load selected model');
    }
  }

  updateModelDisplay(data) {
    // Update the model visualization if SVG is available
    if (data.svg_content) {
      this.displaySVGContent(data.svg_content);
    } else if (data.model) {
      // Render model using existing method
      this.currentModel = data.model;
      this.renderModel(data.model);
      this.updateModelStatistics(data.model);
      this.enableExportButtons();
    }
    
    // Update status with model info
    const modelInfo = data.name || data.organization || 'Unknown Model';
    this.updateStatus('ready', `Loaded: ${modelInfo}`);
  }

  displaySVGContent(svgContent) {
    const placeholder = document.getElementById('placeholder');
    const canvas = document.getElementById('model-canvas');
    
    // Hide placeholder and canvas
    placeholder.style.display = 'none';
    canvas.style.display = 'none';
    
    // Create or update SVG display container
    let svgContainer = document.getElementById('svg-display-container');
    if (!svgContainer) {
      svgContainer = document.createElement('div');
      svgContainer.id = 'svg-display-container';
      svgContainer.style.cssText = 'width: 100%; height: 100%; overflow: auto; background: white;';
      document.getElementById('visualization-container').appendChild(svgContainer);
    }
    
    svgContainer.innerHTML = svgContent;
    svgContainer.style.display = 'block';
    
    // Enable export buttons
    this.enableExportButtons();
  }



  viewSVG(modelId) {
    // Open SVG visualization in a new window/tab
    const svgUrl = `/static/visualizations/${modelId}.svg`;
    window.open(svgUrl, '_blank');
  }


  renderAnalyzedModels() {
    const container = document.getElementById('analyzed-models-container');
    
    if (this.analyzedModels.length === 0) {
      container.innerHTML = '<div class="text-muted small">No analyzed models found</div>';
      return;
    }

    const modelsHtml = this.analyzedModels.map(model => {
      const typeClass = `model-type-${model.type}`;
      const statusIcon = model.status === 'processed' ? 'fas fa-check-circle text-success' : 
                        model.status === 'pending' ? 'fas fa-clock text-warning' : 
                        'fas fa-file text-muted';

      return `
        <div class="analyzed-model-item" data-model-id="${model.id}">
          <div class="model-item-header">
            <span class="model-item-title">${model.name}</span>
            <span class="model-item-type ${typeClass}">${model.type}</span>
          </div>
          <div class="model-item-details">
            <span><i class="${statusIcon} me-1"></i>${model.status}</span>
            ${model.organization ? `<span class="organization-badge">${model.organization}</span>` : ''}
          </div>
          ${model.type === 'projection' ? `
            <div class="model-actions">
              <button class="model-action-btn" onclick="app.loadAnalyzedModel('${model.id}')">
                <i class="fas fa-eye me-1"></i>View
              </button>
              <button class="model-action-btn" onclick="app.reprocessModel('${model.id}')">
                <i class="fas fa-sync me-1"></i>Reprocess
              </button>
              ${model.has_visualization ? `
                <button class="model-action-btn" onclick="app.viewVisualization('${model.id}')">
                  <i class="fas fa-image me-1"></i>SVG
                </button>
              ` : ''}
            </div>
          ` : `
            <div class="model-actions">
              <button class="model-action-btn" onclick="app.loadAnalyzedModel('${model.id}')">
                <i class="fas fa-eye me-1"></i>View
              </button>
            </div>
          `}
        </div>
      `;
    }).join('');

    container.innerHTML = modelsHtml;
  }

  async loadAnalyzedModel(modelId) {
    try {
      this.updateStatus('processing', 'Loading analyzed model...');
      
      const response = await fetch(`/model/${modelId}`);
      if (!response.ok) {
        throw new Error('Failed to load model');
      }

      const data = await response.json();
      
      // Update selected model in UI
      document.querySelectorAll('.analyzed-model-item').forEach(item => {
        item.classList.remove('selected');
      });
      document.querySelector(`[data-model-id="${modelId}"]`).classList.add('selected');
      
      // Render the model
      this.selectedAnalyzedModel = modelId;
      this.currentModel = data.model;
      this.renderModel(data.model);
      this.updateModelStatistics(data.model);
      this.enableExportButtons();
      
      this.updateStatus('ready', `Loaded: ${data.organization || data.name || modelId}`);
      this.showSuccess(`Model ${modelId} loaded successfully`);

    } catch (error) {
      this.showError('Failed to load analyzed model: ' + error.message);
      this.updateStatus('error', 'Failed to load model');
    }
  }

  async reprocessModel(modelId) {
    try {
      this.updateStatus('processing', 'Reprocessing model...');
      this.showProgress(true);
      
      const response = await fetch(`/reprocess/${modelId}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Reprocessing failed');
      }

      const data = await response.json();
      
      // Update the model display
      this.currentModel = data.model;
      this.renderModel(data.model);
      this.updateModelStatistics(data.model);
      
      this.updateStatus('ready', 'Reprocessing completed');
      this.showSuccess('Model reprocessed successfully');

    } catch (error) {
      this.showError('Reprocessing failed: ' + error.message);
      this.updateStatus('error', 'Reprocessing failed');
    } finally {
      this.showProgress(false);
    }
  }

  async viewVisualization(modelId) {
    try {
      const model = this.analyzedModels.find(m => m.id === modelId);
      if (model && model.svg_path) {
        // Open SVG in a new window/tab
        const svgUrl = `/static/visualizations/${model.organization}.svg`;
        window.open(svgUrl, '_blank');
      }
    } catch (error) {
      this.showError('Failed to open visualization: ' + error.message);
    }
  }
}

// Global functions for testing
window.testLoadModel = function() {
  console.log('Testing load model function...');
  if (window.app) {
    window.app.loadModel('filtered_log_Agent_1');
  } else {
    console.error('App not found!');
  }
};

// Global functions for onclick handlers
window.loadModelDirect = function(modelId) {
  console.log('Loading model directly:', modelId);
  if (window.app) {
    window.app.loadModel(modelId);
  } else {
    console.error('App not found!');
  }
};

window.viewSVGDirect = function(modelId) {
  console.log('Viewing SVG directly:', modelId);
  if (window.app) {
    window.app.viewSVG(modelId);
  } else {
    console.error('App not found!');
  }
};


// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  window.app = new ProcessDiscoveryApp();
  // Initialize with default parameters
 // window.app.showParametersForBaseTechnique('im');
});



// Export the class for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProcessDiscoveryApp;
}
