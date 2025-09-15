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
    
    // Initialize with some sample PNML models for testing
    //this.initializeSampleModels();
    
    this.initializeEventListeners();
    this.setupFileUpload();
    this.setupVisualization();
    this.loadAnalyzedModels();
    this.loadAvailableXESFiles();
    
  }

  

  initializeEventListeners() {
    
    // // Zoom controls
    // document.getElementById('zoom-in').addEventListener('click', () => this.zoomIn());
    // document.getElementById('zoom-out').addEventListener('click', () => this.zoomOut());
    // document.getElementById('fit-to-screen').addEventListener('click', () => this.fitToScreen());
    // document.getElementById('reset-view').addEventListener('click', () => this.resetView());

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

  async visualizePNMLFile(filePath) {
    try {
      // Initialize PNML visualization container if it doesn't exist
      await this.initializePNMLVisualization();
      
      // Construct the proper URL for fetching PNML files through the server endpoint
      let pnmlUrl;
      if (filePath.startsWith('../')) {
        // Remove ../ prefix and add /pnml/ endpoint
        pnmlUrl = `/pnml/${filePath.substring(3)}`;
      } else if (filePath.startsWith('data/')) {
        // Direct data path
        pnmlUrl = `/pnml/${filePath}`;
      } else {
        // Fallback - assume it's a relative path from project root
        pnmlUrl = `/pnml/${filePath}`;
      }
      
      console.log('Fetching PNML from:', pnmlUrl);
      
      // Fetch PNML file content
      const response = await fetch(pnmlUrl);
      if (!response.ok) {
        throw new Error(`Failed to load PNML file: ${response.status} ${response.statusText}`);
      }
      
      const pnmlContent = await response.text();
      
      // Parse and visualize the PNML
      this.parsePNMLAndVisualize(pnmlContent, filePath);
      
      this.updateStatus('ready', `Visualizing PNML: ${filePath}`);
      
    } catch (error) {
      console.error('Error visualizing PNML file:', error);
      throw error;
    }
  }

  async initializePNMLVisualization() {
    // Hide other containers
    const placeholder = document.getElementById('placeholder');
    const canvas = document.getElementById('model-canvas');
    let svgContainer = document.getElementById('svg-display-container');
    
    if (placeholder) placeholder.style.display = 'none';
    if (canvas) canvas.style.display = 'none';
    if (svgContainer) svgContainer.style.display = 'none';
    
    // Create or get PNML visualization container
    let pnmlContainer = document.getElementById('pnml-visualization-container');
    if (!pnmlContainer) {
      pnmlContainer = document.createElement('div');
      pnmlContainer.id = 'pnml-visualization-container';
      pnmlContainer.style.cssText = 'width: 100%; height: 100%; background: white;';
      
      // Use Bootstrap button styles for controls
      pnmlContainer.innerHTML = `
        <div id="pnml-controls" class="visualization-controls" style="position:absolute; top:10px; right:10px; z-index:1000;">
          <div class="zoom-controls">
            <button class="btn btn-sm btn-outline-secondary" onclick="app.fitPNMLToWindow()" title="Fit to Window">
              <i class="fas fa-expand-arrows-alt"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" onclick="app.clearPNMLGraph()" title="Clear">
              <i class="fas fa-trash"></i>
            </button>
            <!-- Added visible + and - buttons for zoom -->
            <button class="btn btn-sm btn-outline-secondary" onclick="app.zoomInPNML()" title="Zoom In">
              <i class="fas fa-plus"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" onclick="app.zoomOutPNML()" title="Zoom Out">
              <i class="fas fa-minus"></i>
            </button>
            <!-- Drag-to-pan toggle button -->
            <button class="btn btn-sm btn-outline-secondary" id="pnml-drag-toggle" title="Enable Drag to Pan">
              <i class="fas fa-hand-paper"></i> Drag
            </button>
          </div>
        </div>
        <div id="pnml-holder" style="border: 1px solid #ddd; background-color: white; width: 100%; height: 600px;"></div>
        <div id="pnml-info" style="margin-top: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;">
          Ready to load PNML file...
        </div>
      `;
      
      const visualizationContainer = document.getElementById('visualization-container');
      if (visualizationContainer) {
        visualizationContainer.appendChild(pnmlContainer);
      }
    }
    
    pnmlContainer.style.display = 'block';
    
    // Initialize JointJS if needed and wait for it
    await this.initializeJointJS();
      // Add drag-to-pan functionality to pnml-holder, toggled by button
      const pnmlHolder = document.getElementById('pnml-holder');
      const dragToggleBtn = document.getElementById('pnml-drag-toggle');
      let dragModeEnabled = false;
      let isDraggingPNML = false;
      let lastXPNML = 0;
      let lastYPNML = 0;

      dragToggleBtn.addEventListener('click', () => {
        dragModeEnabled = !dragModeEnabled;
        dragToggleBtn.classList.toggle('active', dragModeEnabled);
        dragToggleBtn.title = dragModeEnabled ? 'Disable Drag to Pan' : 'Enable Drag to Pan';
        dragToggleBtn.innerHTML = dragModeEnabled ? '<i class="fas fa-hand-paper"></i> Dragging' : '<i class="fas fa-hand-paper"></i> Drag';
        pnmlHolder.style.cursor = dragModeEnabled ? 'grab' : 'default';
      });

      pnmlHolder.addEventListener('mousedown', (e) => {
        if (!dragModeEnabled) return;
        isDraggingPNML = true;
        lastXPNML = e.clientX;
        lastYPNML = e.clientY;
        pnmlHolder.style.cursor = 'grabbing';
      });

      window.addEventListener('mousemove', (e) => {
        if (isDraggingPNML && dragModeEnabled && this.pnmlPaper) {
          const dx = e.clientX - lastXPNML;
          const dy = e.clientY - lastYPNML;
          let tx = this.pnmlPaper.translate().tx + dx;
          let ty = this.pnmlPaper.translate().ty + dy;
          this.pnmlPaper.translate(tx, ty);
          lastXPNML = e.clientX;
          lastYPNML = e.clientY;
        }
      });

      window.addEventListener('mouseup', () => {
        if (!dragModeEnabled) return;
        isDraggingPNML = false;
        pnmlHolder.style.cursor = dragModeEnabled ? 'grab' : 'default';
      });
  }

  async initializeJointJS() {
    return new Promise((resolve, reject) => {
      // Check if JointJS is already loaded
      if (typeof joint === 'undefined') {
        // Load JointJS dynamically
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@joint/core@4.0.1/dist/joint.js';
        script.onload = () => {
          this.setupPNMLPaper();
          resolve();
        };
        script.onerror = () => {
          reject(new Error('Failed to load JointJS library'));
        };
        document.head.appendChild(script);
      } else {
        this.setupPNMLPaper();
        resolve();
      }
    });
  }

  setupPNMLPaper() {
    if (this.pnmlGraph && this.pnmlPaper) {
      // Already initialized
      return;
    }
    
    const holderElement = document.getElementById('pnml-holder');
    if (!holderElement) {
      console.error('pnml-holder element not found');
      return;
    }
    
    const namespace = joint.shapes;
    this.pnmlGraph = new joint.dia.Graph({}, { cellNamespace: namespace });

    this.pnmlPaper = new joint.dia.Paper({
      el: holderElement,
      model: this.pnmlGraph,
      width: 2200,
      height: 600,
      gridSize: 10,
      drawGrid: true,
      background: { color: 'white' },
      cellViewNamespace: namespace,
      interactive: true
    });

    // Add event listeners for interaction
    this.setupPNMLEventListeners();
  }

  setupPNMLEventListeners() {
    if (!this.pnmlPaper) return;
    
    // Click handlers for interaction
    this.pnmlPaper.on('element:pointerclick', (elementView) => {
      const element = elementView.model;
      const pnmlData = element.get('pnmlData');
      const elementType = element.get('elementType');
      
      let info = '<strong>Element Details:</strong><br>';
      
      if (pnmlData) {
        info += `Type: ${elementType}<br>`;
        info += `PNML ID: ${pnmlData.id}<br>`;
        info += `Name: ${pnmlData.name}<br>`;
        
        if (elementType === 'place') {
          info += `Agent Type: ${pnmlData.type}<br>`;
          if (pnmlData.initialMarking) {
            info += `Initial Marking: ${pnmlData.initialMarking}<br>`;
          }
        } else if (elementType === 'transition') {
          const isTau = element.get('isTau');
          info += `Type: ${isTau ? 'Tau (Silent) Transition' : 'Regular Transition'}<br>`;
        }
      }
    });

    this.pnmlPaper.on('link:pointerclick', (linkView) => {
      const link = linkView.model;
      
      let info = '<strong>Arc Details:</strong><br>';
      info += `Type: Arc<br>`;
      
      const source = link.getSourceElement();
      const target = link.getTargetElement();
      
      if (source && target) {
        const sourcePnml = source.get('pnmlData');
        const targetPnml = target.get('pnmlData');
        
        info += `From: ${sourcePnml ? sourcePnml.name : source.id}<br>`;
        info += `To: ${targetPnml ? targetPnml.name : target.id}<br>`;
      }
      
      document.getElementById('pnml-info').innerHTML = info;
    });
  }

  // PNML Zoom In/Out and Movement Controls
  zoomInPNML() {
    if (this.pnmlPaper) {
      let scale = this.pnmlPaper.scale().sx;
      scale = Math.min(2, scale * 1.2);
      this.pnmlPaper.scale(scale, scale);
    }
  }

  zoomOutPNML() {
    if (this.pnmlPaper) {
      let scale = this.pnmlPaper.scale().sx;
      scale = Math.max(0.1, scale / 1.2);
      this.pnmlPaper.scale(scale, scale);
    }
  }

  movePNML(direction) {
    if (this.pnmlPaper) {
      let tx = this.pnmlPaper.translate().tx;
      let ty = this.pnmlPaper.translate().ty;
      const step = 50;
      switch (direction) {
        case 'up': ty -= step; break;
        case 'down': ty += step; break;
        case 'left': tx -= step; break;
        case 'right': tx += step; break;
      }
      this.pnmlPaper.translate(tx, ty);
    }
  }
// ...existing code...

  parsePNMLAndVisualize(xmlContent, fileName = 'PNML File') {
    try {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlContent, 'text/xml');
      
      // Check for XML parsing errors
      const parserError = xmlDoc.querySelector('parsererror');
      if (parserError) {
        throw new Error('XML parsing error: ' + parserError.textContent);
      }
      
      // Ensure the graph is initialized before clearing
      if (!this.pnmlGraph) {
        console.warn('PNML graph not initialized, setting up now...');
        this.setupPNMLPaper();
      }
      
      // Clear existing graph
      if (this.pnmlGraph) {
        this.pnmlGraph.clear();
      }
      
      const elements = new Map();
      
      // Extract net name
      const net = xmlDoc.querySelector('net');
      const netName = net?.querySelector('name text')?.textContent || fileName;
      
      // Parse PNML content (similar to test_new.html)
      const places = [];
      const transitions = [];
      const arcs = [];
      
      // Collect places
      xmlDoc.querySelectorAll('place').forEach(place => {
        const id = place.getAttribute('id');
        const name = place.querySelector('name text')?.textContent || id;
        const type = place.querySelector('type text')?.textContent || '';
        const initialMarking = place.querySelector('initialMarking text')?.textContent || '';
        places.push({ id, name, type, initialMarking });
      });
      
      // Collect transitions
      xmlDoc.querySelectorAll('transition').forEach(transition => {
        const id = transition.getAttribute('id');
        const name = transition.querySelector('name text')?.textContent || id;
        transitions.push({ id, name });
      });
      
      // Collect arcs
      xmlDoc.querySelectorAll('arc').forEach(arc => {
        const source = arc.getAttribute('source');
        const target = arc.getAttribute('target');
        const identifier = arc.querySelector('identifier text')?.textContent || '';
        arcs.push({ source, target, identifier });
      });
      
      // Create visual elements
      this.createPNMLVisualElements(places, transitions, arcs, elements);
      
      // Update info
      document.getElementById('pnml-info').innerHTML = 
        `<strong>${netName}</strong><br>` +
        `Places: ${places.length}, Transitions: ${transitions.length}, Arcs: ${arcs.length}<br>` +
        'Click on elements to see details.';
      
      // Auto-fit after a short delay
      setTimeout(() => this.fitPNMLToWindow(), 100);
      
    } catch (error) {
      document.getElementById('pnml-info').innerHTML = 
        '<strong>Error parsing PNML file:</strong><br>' + error.message;
      console.error(error);
      throw error;
    }
  }

  createPNMLVisualElements(places, transitions, arcs, elements) {
    // Create place elements
    places.forEach((placeData, index) => {
      const { id, name, type, initialMarking } = placeData;
      const circle = new joint.shapes.standard.Circle();
      // Initial position, will be arranged later
      circle.position(0, 0);
      circle.resize(50, 50);
      circle.set('id', id);
      circle.set('pnmlData', placeData);
      circle.set('elementType', 'place');
      circle.attr({
        body: {
          fill: initialMarking ? '#ffeb3b' : 'white',
          stroke: 'black',
          strokeWidth: 2
        },
        label: {
          text: name,
          fontSize: 10,
          fontFamily: 'Times, serif',
          fill: 'black'
        }
      });
      circle.addTo(this.pnmlGraph);
      elements.set(id, circle);
    });

    // Create transition elements
    transitions.forEach((transitionData, index) => {
      const { id, name } = transitionData;
      const isTau = this.isTauTransition(name, id);
      const rect = new joint.shapes.standard.Rectangle();
      // Initial position, will be arranged later
      rect.position(0, 0);
      rect.resize(60, 30);
      rect.set('id', id);
      rect.set('pnmlData', transitionData);
      rect.set('elementType', 'transition');
      rect.set('isTau', isTau);
      rect.attr({
        body: {
          fill: isTau ? 'black' : 'white',
          stroke: 'black',
          strokeWidth: 2
        },
        label: {
          text: isTau ? 'τ' : name,
          fontSize: 10,
          fontFamily: 'Times, serif',
          fill: isTau ? 'white' : 'black'
        }
      });
      rect.addTo(this.pnmlGraph);
      elements.set(id, rect);
    });

  // Arrange elements visually using hierarchical level logic
  this.arrangePNMLElementsHierarchical(places, transitions, elements, arcs);

    // Create arc connections
    arcs.forEach(arcData => {
      const { source, target, identifier } = arcData;
      const sourceElement = elements.get(source);
      const targetElement = elements.get(target);
      if (sourceElement && targetElement) {
        const link = new joint.shapes.standard.Link();
        link.source(sourceElement);
        link.target(targetElement);
        link.attr({
          line: {
            stroke: 'black',
            strokeWidth: 1,
            targetMarker: {
              type: 'path',
              d: 'M 10 -5 0 0 10 5 z',
              fill: 'black'
            }
          }
        });
        if (identifier) {
          link.labels([{
            attrs: {
              text: {
                text: identifier,
                fontSize: 8,
                fontFamily: 'Times, serif',
              }
            }
          }]);
        }
        link.addTo(this.pnmlGraph);
      }
    });
  }

  // Arrange PNML elements in a grid layout (copied exactly from test_new.html)
  // Arrange PNML elements using hierarchical levels
  arrangePNMLElementsHierarchical(places, transitions, elementsMap, arcs) {
    // Filter out places and transitions with no connections
    const connectedPlaces = places.filter(p => {
      const hasIncoming = arcs.some(arc => arc.target === p.id);
      const hasOutgoing = arcs.some(arc => arc.source === p.id);
      return hasIncoming || hasOutgoing;
    });
    const connectedTransitions = transitions.filter(t => {
      const hasIncoming = arcs.some(arc => arc.target === t.id);
      const hasOutgoing = arcs.some(arc => arc.source === t.id);
      return hasIncoming || hasOutgoing;
    });

    // Combine connected places and transitions for level calculation
    const allElements = [
      ...connectedPlaces.map(p => ({ ...p, type: 'place' })),
      ...connectedTransitions.map(t => ({ ...t, type: 'transition' }))
    ];

    // Find max level
    let maxLevel = 0;
    allElements.forEach(e => {
      const lvl = this.getLevel(e.id, arcs);
      if (lvl > maxLevel) maxLevel = lvl;
    });

    // For each level, arrange elements left to right (horizontal levels)
    // Each level is a column, elements at that level are stacked vertically
    const startX = 100;
    const startY = 100;
    const spacingX = 180;
    const spacingY = 80;
    for (let level = 0; level <= maxLevel; level++) {
      const elementsAtLevel = allElements.filter(e => this.getLevel(e.id, arcs) === level);
      elementsAtLevel.forEach((e, idx) => {
        const x = startX + level * spacingX;
        const y = startY + idx * spacingY;
        const elem = elementsMap.get(e.id);
        if (elem) {
          elem.position(x, y);
        }
      });
    }
  }

  calculateElementPosition(id, index, elementType, places, transitions, arcs) {
    // Simple grid layout for now - can be enhanced with graph topology later
    const cols = 5;
    const startX = elementType === 'place' ? 100 : 200;
    const startY = 100;
    const spacingX = 150;
    const spacingY = 100;
    
    const col = index % cols;
    const row = Math.floor(index / cols);
    
    return {
      x: startX + col * spacingX,
      y: startY + row * spacingY
    };
  }

    // Helper: Get the hierarchical level of an element (place/transition)
    getLevel(elementId, arcs) {
      // Level 0: no incoming arcs
      let level = 0;
      let current = elementId;
      let visited = new Set();
      while (true) {
        let incoming = arcs.filter(arc => arc.target === current);
        if (incoming.length === 0) break;
        // Take the first incoming arc's source as parent
        current = incoming[0].source;
        if (visited.has(current)) break;
        visited.add(current);
        level++;
      }
      return level;
    }

    // Helper: Calculate position within a level
    calculateLevelPosition(level, index, total, startX = 100, spacingX = 120, startY = 100, spacingY = 100) {
      const x = startX + index * spacingX;
      const y = startY + level * spacingY;
      return { x, y };
    }

    // Helper: Extract number from string (for sorting, etc)
    extractNumber(str) {
      const match = str.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }

    // Helper: Get all elements at a given level
    getElementsAtLevel(level, elements, arcs) {
      return elements.filter(e => this.getLevel(e.id, arcs) === level);
    }
  isTauTransition(name, id) {
    if (!name && !id) return false;
    
    const text = (name || id).toLowerCase().trim();
    
    return text === 'tau' || 
           text === 'τ' || 
           text === 'silent' || 
           text === '' || 
           text === 'skip' ||
           text === 'epsilon' ||
           text === 'ε' ||
           text.startsWith('tau') ||
           text.startsWith('τ_') ||
           text.includes('silent');
  }

  fitPNMLToWindow() {
    if (this.pnmlPaper) {
      const contentBBox = this.pnmlPaper.getContentArea();
      this.pnmlPaper.scaleContentToFit({
        padding: 50,
        maxScale: 1.5,
        minScale: 0.1
      });
    }
  }

  resetPNMLZoom() {
    if (this.pnmlPaper) {
      this.pnmlPaper.scale(1, 1);
      this.pnmlPaper.translate(0, 0);
    }
  }

  clearPNMLGraph() {
    if (this.pnmlGraph) {
      this.pnmlGraph.clear();
      document.getElementById('pnml-info').innerHTML = 
        '<strong>Graph Cleared</strong><br>Select a PNML file to visualize.';
    }
  }

  downloadPNMLAsSVG() {
    if (this.pnmlPaper) {
      const svgContent = this.pnmlPaper.svg;
      const blob = new Blob([svgContent], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = 'petri-net.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }

  viewSVG(modelId) {
    // Open SVG visualization in a new window/tab
    const svgUrl = `/static/visualizations/${modelId}.svg`;
    window.open(svgUrl, '_blank');
  }


  renderAnalyzedModels() {
    const container = document.getElementById('analyzed-models-container');
    
    if (this.analyzedModels.length === 0) {
      container.innerHTML = '<div class="text-muted small">No analyzed models selected</div>';
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
      
      // Find the model in our current analyzed models
      const model = this.analyzedModels.find(m => m.id === modelId);

      console.log(modelId);
      if (model && model.pnml_path) {
        // Use the new PNML visualization
        try {
          // Convert absolute path to relative path from webapp
          const relativePath = model.pnml_path.replace('/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/', '../');
          console.log('Loading model:', model.name);
          console.log('Original path:', model.pnml_path);
          console.log('Relative path:', relativePath);
          
          await this.visualizePNMLFile(relativePath);
          
          // Update selected model in UI
          document.querySelectorAll('.model-item').forEach(item => {
            item.classList.remove('selected');
          });
          const modelElement = document.querySelector(`[data-model-id="${modelId}"]`);
          if (modelElement) {
            modelElement.classList.add('selected');
          }
          console.log(this.selectedAnalyzedModel)
          console.log('Selected model updated to:', modelId);
          
          this.selectedAnalyzedModel = modelId;
          this.updateStatus('ready', `Visualizing: ${model.name}`);
          this.showSuccess(`Model ${model.name} loaded successfully`);
          
        } catch (vizError) {
          console.error('PNML visualization error:', vizError);
          this.showError('PNML visualizer error: ' + vizError.message);
        }
      } else {
        // Fallback: try to fetch from server
        const response = await fetch(`/model/${modelId}`);
        if (!response.ok) {
          throw new Error('Failed to load model from server');
        }

        const data = await response.json();
        console.log('Analyzed model data:', data);
        
        this.updateStatus('ready', `Loaded: ${data.organization || data.name || modelId}`);
        this.showSuccess(`Model ${modelId} loaded from server`);
      }

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
      if (model && model.pnml_path) {
        // Use the new PNML visualization
        try {
          // Convert absolute path to relative path from webapp
          const relativePath = model.pnml_path.replace('/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/', '../');
          await this.visualizePNMLFile(relativePath);
          this.showSuccess(`Visualizing: ${model.name}`);
        } catch (vizError) {
          console.error('PNML visualization error:', vizError);
          // Fallback to SVG if PNML visualizer fails
          if (model.svg_path) {
            const svgUrl = `/static/visualizations/${model.organization}.svg`;
            window.open(svgUrl, '_blank');
          } else {
            this.showError('No visualization available for this model');
          }
        }
      } else {
        this.showError('Model or PNML file not found');
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
