from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
import pandas as pd
import numpy as np
import asyncio
import io
import json
import os
import uuid
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from werkzeug.utils import secure_filename
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Import your data analyzer bot
# from data_analyzer_bot import DataAnalyzerBot

# Mock bot for demonstration
class MockDataAnalyzerBot:
    async def analyze_data(self, data, question, context=None):
        await asyncio.sleep(3)  # Simulate processing time
        
        analysis_response = {
            "content": f"Comprehensive analysis completed for dataset with {data.shape[0]} rows and {data.shape[1]} columns.",
            "insights": [
                f"Dataset contains {data.shape[0]} records with {data.shape[1]} features",
                "Data quality assessment shows minimal missing values" if data.isnull().sum().sum() < data.shape[0] * 0.1 else "Some data quality issues identified",
                "Multiple patterns and trends identified for further investigation"
            ],
            "confidence_score": 0.87
        }
        
        story_response = {
            "content": f"The analysis reveals compelling insights about {question}. Key findings suggest actionable opportunities for improvement.",
            "insights": ["Strong correlations identified in the data", "Clear business implications discovered"],
            "confidence_score": 0.92
        }
        
        viz_response = {
            "content": "Visualization recommendations include time series analysis, comparative bar charts, and correlation heatmaps.",
            "recommendations": [
                "Line charts for temporal trends",
                "Bar charts for categorical comparisons", 
                "Heatmaps for correlation analysis",
                "Scatter plots for relationship exploration"
            ],
            "confidence_score": 0.89
        }
        
        return {
            "analysis": type('obj', (object,), analysis_response),
            "story": type('obj', (object,), story_response),
            "visualizations": type('obj', (object,), viz_response)
        }
    
    def generate_report(self, results):
        return f"""# Data Analysis Report - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
{results['story'].content}

## Detailed Analysis
{results['analysis'].content}

## Key Insights
""" + "\n".join([f"- {insight}" for insight in results['analysis'].insights]) + f"""

## Visualization Recommendations
{results['visualizations'].content}

## Recommended Charts
""" + "\n".join([f"- {rec}" for rec in results['visualizations'].recommendations])

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables for storing data and results
user_data = {}
analysis_status = {}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            
            # Save and process file
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Load data based on file type
            if file_ext == 'csv':
                data = pd.read_csv(file)
            elif file_ext in ['xlsx', 'xls']:
                data = pd.read_excel(file)
            elif file_ext == 'json':
                data = pd.read_json(file)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400
            
            # Store data
            user_data[session_id] = {
                'data': data,
                'filename': filename,
                'upload_time': datetime.now()
            }
            
            # Return data summary
            summary = get_data_summary(data)
            return jsonify({
                'success': True,
                'session_id': session_id,
                'summary': summary,
                'preview': data.head(10).to_html(classes='table table-striped')
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400

@app.route('/sample_data')
def load_sample_data():
    """Load sample data for demonstration"""
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=200, freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(5000, 1000, 200) + np.sin(np.arange(200) * 2 * np.pi / 30) * 500,
        'region': np.random.choice(['North', 'South', 'East', 'West'], 200),
        'product': np.random.choice(['Electronics', 'Clothing', 'Books'], 200),
        'customer_rating': np.random.uniform(3.0, 5.0, 200),
        'marketing_spend': np.random.normal(2000, 500, 200)
    })
    
    user_data[session_id] = {
        'data': data,
        'filename': 'sample_sales_data.csv',
        'upload_time': datetime.now()
    }
    
    summary = get_data_summary(data)
    return jsonify({
        'success': True,
        'session_id': session_id,
        'summary': summary,
        'preview': data.head(10).to_html(classes='table table-striped')
    })

@app.route('/analyze', methods=['POST'])
def start_analysis():
    """Start data analysis"""
    session_id = session.get('session_id')
    if not session_id or session_id not in user_data:
        return jsonify({'error': 'No data uploaded'}), 400
    
    question = request.json.get('question', '')
    context = request.json.get('context', '')
    analysis_type = request.json.get('analysis_type', 'exploratory')
    
    if not question.strip():
        return jsonify({'error': 'Please provide an analysis question'}), 400
    
    # Start analysis in background
    analysis_id = str(uuid.uuid4())
    analysis_status[analysis_id] = {
        'status': 'starting',
        'progress': 0,
        'message': 'Initializing analysis...'
    }
    
    # Run analysis in background thread
    def run_analysis():
        asyncio.run(perform_analysis(session_id, analysis_id, question, context))
    
    thread = threading.Thread(target=run_analysis)
    thread.start()
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id
    })

@app.route('/analysis_status/<analysis_id>')
def get_analysis_status(analysis_id):
    """Get analysis progress status"""
    if analysis_id not in analysis_status:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify(analysis_status[analysis_id])

@app.route('/results/<analysis_id>')
def get_results(analysis_id):
    """Get analysis results"""
    if analysis_id not in analysis_status:
        return jsonify({'error': 'Analysis not found'}), 404
    
    status = analysis_status[analysis_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    return render_template('results.html', 
                         results=status['results'],
                         analysis_id=analysis_id)

@app.route('/download_report/<analysis_id>')
def download_report(analysis_id):
    """Download analysis report"""
    if analysis_id not in analysis_status:
        return jsonify({'error': 'Analysis not found'}), 404
    
    status = analysis_status[analysis_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    # Create report file
    report_content = status['results']['report']
    
    # Save to temporary file
    report_filename = f'analysis_report_{analysis_id}.md'
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return send_file(report_path, as_attachment=True, download_name=report_filename)

@app.route('/visualize/<analysis_id>')
def create_visualizations(analysis_id):
    """Create and return visualizations"""
    session_id = session.get('session_id')
    if not session_id or session_id not in user_data:
        return jsonify({'error': 'No data available'}), 400
    
    data = user_data[session_id]['data']
    
    # Create sample visualizations
    charts = generate_sample_charts(data)
    
    return jsonify({'charts': charts})

async def perform_analysis(session_id, analysis_id, question, context):
    """Perform the actual data analysis"""
    try:
        # Update status
        analysis_status[analysis_id].update({
            'status': 'running',
            'progress': 10,
            'message': 'Loading data...'
        })
        
        data = user_data[session_id]['data']
        
        # Initialize bot (using mock for demo)
        bot = MockDataAnalyzerBot()
        
        analysis_status[analysis_id].update({
            'progress': 30,
            'message': 'Running data analysis...'
        })
        
        # Run analysis
        results = await bot.analyze_data(data, question, context)
        
        analysis_status[analysis_id].update({
            'progress': 70,
            'message': 'Generating report...'
        })
        
        # Generate report
        report = bot.generate_report(results)
        
        analysis_status[analysis_id].update({
            'progress': 90,
            'message': 'Finalizing results...'
        })
        
        # Store results
        analysis_status[analysis_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Analysis completed successfully!',
            'results': {
                'analysis': {
                    'content': results['analysis'].content,
                    'insights': results['analysis'].insights,
                    'confidence': results['analysis'].confidence_score
                },
                'story': {
                    'content': results['story'].content,
                    'insights': results['story'].insights,
                    'confidence': results['story'].confidence_score
                },
                'visualizations': {
                    'content': results['visualizations'].content,
                    'recommendations': results['visualizations'].recommendations,
                    'confidence': results['visualizations'].confidence_score
                },
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        analysis_status[analysis_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Analysis failed: {str(e)}'
        })

def get_data_summary(data):
    """Generate data summary"""
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
    
    return {
        'shape': data.shape,
        'columns': list(data.columns),
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols,
        'missing_values': data.isnull().sum().sum(),
        'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
        'dtypes': data.dtypes.astype(str).to_dict()
    }

def generate_sample_charts(data):
    """Generate sample charts for visualization"""
    charts = []
    
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    categorical_cols = data.select_dtypes(include=['object']).columns
    
    # Histogram for numeric columns
    if len(numeric_cols) > 0:
        col = numeric_cols[0]
        fig = px.histogram(data, x=col, title=f'Distribution of {col}')
        charts.append({
            'type': 'histogram',
            'title': f'Distribution of {col}',
            'data': plotly.utils.PlotlyJSONEncoder().encode(fig)
        })
    
    # Bar chart for categorical columns
    if len(categorical_cols) > 0:
        col = categorical_cols[0]
        value_counts = data[col].value_counts().head(10)
        fig = px.bar(x=value_counts.index, y=value_counts.values, 
                    title=f'Top 10 {col} Values')
        charts.append({
            'type': 'bar',
            'title': f'Top 10 {col} Values',
            'data': plotly.utils.PlotlyJSONEncoder().encode(fig)
        })
    
    # Correlation heatmap if multiple numeric columns
    if len(numeric_cols) > 1:
        corr_matrix = data[numeric_cols].corr()
        fig = px.imshow(corr_matrix, text_auto=True, title='Correlation Matrix')
        charts.append({
            'type': 'heatmap',
            'title': 'Correlation Matrix',
            'data': plotly.utils.PlotlyJSONEncoder().encode(fig)
        })
    
    # Time series if date column exists
    date_cols = data.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0 and len(numeric_cols) > 0:
        fig = px.line(data, x=date_cols[0], y=numeric_cols[0], 
                     title=f'{numeric_cols[0]} Over Time')
        charts.append({
            'type': 'line',
            'title': f'{numeric_cols[0]} Over Time',
            'data': plotly.utils.PlotlyJSONEncoder().encode(fig)
        })
    
    return charts

# HTML Templates as strings (for demonstration - in production, use separate template files)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Analyzer Bot</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
        }
        .section-card {
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        .insight-box {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #007bff;
            margin: 1rem 0;
        }
        .progress-container {
            display: none;
        }
        .upload-area {
            border: 2px dashed #dee2e6;
            border-radius: 0.5rem;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .upload-area:hover {
            border-color: #007bff;
            background-color: #f8f9fa;
        }
        .upload-area.dragover {
            border-color: #007bff;
            background-color: #e3f2fd;
        }
    </style>
</head>
<body>
    <div class="main-header">
        <div class="container">
            <h1><i class="fas fa-robot"></i> Data Analyzer Bot</h1>
            <p class="lead">Powered by Azure OpenAI | Intelligent Data Analysis & Storytelling</p>
        </div>
    </div>

    <div class="container mt-4">
        <!-- Configuration Section -->
        <div class="row">
            <div class="col-md-8">
                <div class="card section-card">
                    <div class="card-header">
                        <h5><i class="fas fa-upload"></i> Data Upload</h5>
                    </div>
                    <div class="card-body">
                        <div class="upload-area" id="uploadArea">
                            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                            <h5>Drop your file here or click to browse</h5>
                            <p class="text-muted">Supported formats: CSV, Excel, JSON</p>
                            <input type="file" id="fileInput" class="d-none" accept=".csv,.xlsx,.xls,.json">
                        </div>
                        
                        <div class="mt-3">
                            <button class="btn btn-outline-primary" onclick="loadSampleData()">
                                <i class="fas fa-database"></i> Try Sample Data
                            </button>
                        </div>
                        
                        <div id="dataPreview" class="mt-4" style="display: none;">
                            <h6>Data Preview:</h6>
                            <div id="dataTable"></div>
                            <div id="dataSummary" class="mt-3"></div>
                        </div>
                    </div>
                </div>

                <!-- Analysis Configuration -->
                <div class="card section-card" id="analysisSection" style="display: none;">
                    <div class="card-header">
                        <h5><i class="fas fa-brain"></i> Analysis Configuration</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="analysisQuestion" class="form-label">Analysis Question</label>
                            <textarea class="form-control" id="analysisQuestion" rows="3" 
                                placeholder="What would you like to analyze? e.g., What are the key trends in sales performance?"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label for="analysisContext" class="form-label">Additional Context (Optional)</label>
                                    <input type="text" class="form-control" id="analysisContext" 
                                        placeholder="e.g., This is quarterly sales data for business review">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="analysisType" class="form-label">Analysis Type</label>
                                    <select class="form-select" id="analysisType">
                                        <option value="exploratory">Exploratory</option>
                                        <option value="descriptive">Descriptive</option>
                                        <option value="diagnostic">Diagnostic</option>
                                        <option value="predictive">Predictive</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <button class="btn btn-primary btn-lg" onclick="startAnalysis()">
                            <i class="fas fa-rocket"></i> Run Analysis
                        </button>
                    </div>
                </div>

                <!-- Progress Section -->
                <div class="card section-card progress-container" id="progressSection">
                    <div class="card-body">
                        <h6>Analysis Progress</h6>
                        <div class="progress mb-3">
                            <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%"></div>
                        </div>
                        <p id="progressMessage">Starting analysis...</p>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <!-- Configuration Panel -->
                <div class="card section-card">
                    <div class="card-header">
                        <h6><i class="fas fa-cog"></i> Configuration</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="azureEndpoint" class="form-label">Azure OpenAI Endpoint</label>
                            <input type="password" class="form-control" id="azureEndpoint" 
                                placeholder="https://your-resource.openai.azure.com/">
                        </div>
                        
                        <div class="mb-3">
                            <label for="azureApiKey" class="form-label">API Key</label>
                            <input type="password" class="form-control" id="azureApiKey" 
                                placeholder="Your Azure OpenAI API key">
                        </div>
                        
                        <div class="mb-3">
                            <label for="modelName" class="form-label">Model</label>
                            <select class="form-select" id="modelName">
                                <option value="gpt-4">GPT-4</option>
                                <option value="gpt-4-32k">GPT-4-32k</option>
                                <option value="gpt-35-turbo">GPT-3.5-Turbo</option>
                            </select>
                        </div>

                        <hr>
                        
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="includeViz" checked>
                            <label class="form-check-label" for="includeViz">
                                Include Visualizations
                            </label>
                        </div>
                        
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="includeStory" checked>
                            <label class="form-check-label" for="includeStory">
                                Include Data Story
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Quick Stats -->
                <div class="card section-card" id="quickStats" style="display: none;">
                    <div class="card-header">
                        <h6><i class="fas fa-chart-bar"></i> Quick Stats</h6>
                    </div>
                    <div class="card-body" id="quickStatsContent">
                        <!-- Stats will be populated here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentSessionId = null;
        let currentAnalysisId = null;

        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        fileInput.addEventListener('change', handleFileSelect);

        function handleDragOver(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        }

        function handleDragLeave(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        }

        function handleDrop(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadFile(files[0]);
            }
        }

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                uploadFile(file);
            }
        }

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSessionId = data.session_id;
                    displayDataPreview(data);
                    document.getElementById('analysisSection').style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Upload failed');
            });
        }

        function loadSampleData() {
            fetch('/sample_data')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSessionId = data.session_id;
                    displayDataPreview(data);
                    document.getElementById('analysisSection').style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function displayDataPreview(data) {
            document.getElementById('dataTable').innerHTML = data.preview;
            document.getElementById('dataPreview').style.display = 'block';
            
            // Display summary stats
            const summary = data.summary;
            const statsHtml = `
                <div class="row text-center">
                    <div class="col-3">
                        <h6>${summary.shape[0]}</h6>
                        <small class="text-muted">Rows</small>
                    </div>
                    <div class="col-3">
                        <h6>${summary.shape[1]}</h6>
                        <small class="text-muted">Columns</small>
                    </div>
                    <div class="col-3">
                        <h6>${summary.missing_values}</h6>
                        <small class="text-muted">Missing</small>
                    </div>
                    <div class="col-3">
                        <h6>${summary.memory_usage_mb.toFixed(1)}MB</h6>
                        <small class="text-muted">Size</small>
                    </div>
                </div>
            `;
            
            document.getElementById('quickStatsContent').innerHTML = statsHtml;
            document.getElementById('quickStats').style.display = 'block';
        }

        function startAnalysis() {
            const question = document.getElementById('analysisQuestion').value;
            const context = document.getElementById('analysisContext').value;
            const analysisType = document.getElementById('analysisType').value;

            if (!question.trim()) {
                alert('Please enter an analysis question');
                return;
            }

            const data = {
                question: question,
                context: context,
                analysis_type: analysisType
            };

            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentAnalysisId = data.analysis_id;
                    document.getElementById('progressSection').style.display = 'block';
                    monitorProgress();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }

        function monitorProgress() {
            const interval = setInterval(() => {
                fetch(`/analysis_status/${currentAnalysisId}`)
                .then(response => response.json())
                .then(data => {
                    const progressBar = document.getElementById('progressBar');
                    const progressMessage = document.getElementById('progressMessage');
                    
                    progressBar.style.width = data.progress + '%';
                    progressBar.textContent = data.progress + '%';
                    progressMessage.textContent = data.message;

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        setTimeout(() => {
                            window.location.href = `/results/${currentAnalysisId}`;
                        }, 1000);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        progressBar.classList.add('bg-danger');
                    }
                });
            }, 2000);
        }
    </script>
</body>
</html>
"""

RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Results - Data Analyzer Bot</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem 0;
        }
        .insight-box {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #007bff;
            margin: 1rem 0;
        }
        .confidence-badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
        }
        .section-card {
            position: relative;
            margin-bottom: 2rem;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <div class="main-header">
        <div class="container">
            <h2><i class="fas fa-chart-line"></i> Analysis Results</h2>
            <p class="mb-0">Comprehensive data analysis completed</p>
        </div>
    </div>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-12">
                <!-- Action Buttons -->
                <div class="mb-3">
                    <a href="/" class="btn btn-outline-primary">
                        <i class="fas fa-arrow-left"></i> New Analysis
                    </a>
                    <a href="/download_report/{{ analysis_id }}" class="btn btn-success">
                        <i class="fas fa-download"></i> Download Report
                    </a>
                    <button class="btn btn-info" onclick="loadVisualizations()">
                        <i class="fas fa-chart-bar"></i> View Charts
                    </button>
                </div>

                <!-- Tabs -->
                <ul class="nav nav-tabs" id="resultsTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="analysis-tab" data-bs-toggle="tab" data-bs-target="#analysis" type="button" role="tab">
                            <i class="fas fa-microscope"></i> Analysis
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="story-tab" data-bs-toggle="tab" data-bs-target="#story" type="button" role="tab">
                            <i class="fas fa-book"></i> Story
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="visualizations-tab" data-bs-toggle="tab" data-bs-target="#visualizations" type="button" role="tab">
                            <i class="fas fa-chart-pie"></i> Visualizations
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="report-tab" data-bs-toggle="tab" data-bs-target="#report" type="button" role="tab">
                            <i class="fas fa-file-alt"></i> Full Report
                        </button>
                    </li>
                </ul>

                <div class="tab-content" id="resultsTabContent">
                    <!-- Analysis Tab -->
                    <div class="tab-pane fade show active" id="analysis" role="tabpanel">
                        <div class="card section-card mt-3">
                            <div class="card-header">
                                <h5>Key Insights</h5>
                                <span class="badge bg-primary confidence-badge">
                                    {{ "%.0f"|format(results.analysis.confidence * 100) }}% Confidence
                                </span>
                            </div>
                            <div class="card-body">
                                {% for insight in results.analysis.insights %}
                                <div class="insight-box">
                                    <strong>{{ loop.index }}.</strong> {{ insight }}
                                </div>
                                {% endfor %}
                                
                                <h6 class="mt-4">Detailed Analysis</h6>
                                <p>{{ results.analysis.content }}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Story Tab -->
                    <div class="tab-pane fade" id="story" role="tabpanel">
                        <div class="card section-card mt-3">
                            <div class="card-header">
                                <h5>Data Story</h5>
                                <span class="badge bg-success confidence-badge">
                                    {{ "%.0f"|format(results.story.confidence * 100) }}% Confidence
                                </span>
                            </div>
                            <div class="card-body">
                                <div class="story-content">
                                    {{ results.story.content | safe }}
                                </div>
                                
                                <h6 class="mt-4">Story Insights</h6>
                                {% for insight in results.story.insights %}
                                <div class="alert alert-info">
                                    <i class="fas fa-lightbulb"></i> {{ insight }}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>

                    <!-- Visualizations Tab -->
                    <div class="tab-pane fade" id="visualizations" role="tabpanel">
                        <div class="card section-card mt-3">
                            <div class="card-header">
                                <h5>Visualization Recommendations</h5>
                                <span class="badge bg-info confidence-badge">
                                    {{ "%.0f"|format(results.visualizations.confidence * 100) }}% Confidence
                                </span>
                            </div>
                            <div class="card-body">
                                <p>{{ results.visualizations.content }}</p>
                                
                                <h6>Recommended Charts:</h6>
                                <ul>
                                    {% for rec in results.visualizations.recommendations %}
                                    <li>{{ rec }}</li>
                                    {% endfor %}
                                </ul>
                                
                                <div id="chartsContainer" class="mt-4">
                                    <!-- Charts will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Report Tab -->
                    <div class="tab-pane fade" id="report" role="tabpanel">
                        <div class="card section-card mt-3">
                            <div class="card-body">
                                <pre class="bg-light p-3" style="white-space: pre-wrap;">{{ results.report }}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function loadVisualizations() {
            fetch('/visualize/{{ analysis_id }}')
            .then(response => response.json())
            .then(data => {
                if (data.charts) {
                    const container = document.getElementById('chartsContainer');
                    container.innerHTML = '';
                    
                    data.charts.forEach((chart, index) => {
                        const chartDiv = document.createElement('div');
                        chartDiv.id = `chart-${index}`;
                        chartDiv.style.marginBottom = '2rem';
                        container.appendChild(chartDiv);
                        
                        const plotData = JSON.parse(chart.data);
                        Plotly.newPlot(`chart-${index}`, plotData.data, plotData.layout);
                    });
                    
                    // Switch to visualizations tab
                    const vizTab = new bootstrap.Tab(document.getElementById('visualizations-tab'));
                    vizTab.show();
                }
            })
            .catch(error => {
                console.error('Error loading visualizations:', error);
            });
        }
    </script>
</body>
</html>
"""

# Create template directory and save templates
os.makedirs('templates', exist_ok=True)
with open('templates/index.html', 'w') as f:
    f.write(INDEX_HTML)
with open('templates/results.html', 'w') as f:
    f.write(RESULTS_HTML)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)