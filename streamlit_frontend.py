import streamlit as st
import pandas as pd
import numpy as np
import asyncio
import io
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from typing import Dict, Any
import os
import time

# Import your data analyzer bot (assuming it's in a separate file)
# from data_analyzer_bot import DataAnalyzerBot, AgentResponse

# For demo purposes, I'll include a simplified version
# Replace this with your actual import when you have the bot in a separate file

class MockDataAnalyzerBot:
    """Mock version for demonstration - replace with actual bot"""
    
    async def analyze_data(self, data: pd.DataFrame, question: str, context: str = None) -> Dict[str, Any]:
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Mock responses
        analysis_response = {
            "content": f"Analysis complete for dataset with {data.shape[0]} rows and {data.shape[1]} columns. Key findings include trends in {data.columns[0] if len(data.columns) > 0 else 'data'}.",
            "insights": [
                f"Dataset contains {data.shape[0]} records across {data.shape[1]} features",
                "Data quality appears good with minimal missing values" if data.isnull().sum().sum() < data.shape[0] * 0.1 else "Some data quality issues detected",
                "Several interesting patterns identified in the data"
            ],
            "confidence_score": 0.85
        }
        
        story_response = {
            "content": f"The data tells a compelling story about {question}. Our analysis reveals important trends that can inform business decisions.",
            "insights": ["Strong business implications identified", "Clear actionable recommendations available"],
            "confidence_score": 0.90
        }
        
        viz_response = {
            "content": "Recommended visualizations: 1) Time series plot for trends, 2) Bar charts for categorical comparisons, 3) Scatter plots for correlations",
            "recommendations": ["Use line charts for temporal data", "Bar charts work well for categorical data", "Consider heatmaps for correlation analysis"],
            "confidence_score": 0.88
        }
        
        return {
            "analysis": type('obj', (object,), analysis_response),
            "story": type('obj', (object,), story_response),
            "visualizations": type('obj', (object,), viz_response)
        }
    
    def generate_report(self, results):
        return f"""# Data Analysis Report
        
## Analysis Results
{results['analysis'].content}

## Data Story
{results['story'].content}

## Visualization Recommendations
{results['visualizations'].content}
"""

# Streamlit Configuration
st.set_page_config(
    page_title="Data Analyzer Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin: 1rem 0;
        padding: 0.5rem 0;
        border-bottom: 2px solid #3498db;
    }
    .insight-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Data Analyzer Bot</h1>', unsafe_allow_html=True)
    st.markdown("**Powered by Azure OpenAI | Intelligent Data Analysis, Storytelling & Visualization**")
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Azure OpenAI Settings
        st.markdown("### Azure OpenAI Settings")
        azure_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            value=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            type="password",
            help="Your Azure OpenAI endpoint URL"
        )
        
        azure_api_key = st.text_input(
            "Azure OpenAI API Key",
            value=os.getenv("AZURE_OPENAI_API_KEY", ""),
            type="password",
            help="Your Azure OpenAI API key"
        )
        
        model_name = st.selectbox(
            "Model",
            ["gpt-4", "gpt-4-32k", "gpt-35-turbo"],
            help="Select the Azure OpenAI model to use"
        )
        
        # Analysis Settings
        st.markdown("### Analysis Settings")
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Quick", "Standard", "Deep"],
            value="Standard"
        )
        
        include_viz = st.checkbox("Include Visualizations", value=True)
        include_story = st.checkbox("Include Data Story", value=True)
        
        # Sample Data
        st.markdown("### 📊 Try Sample Data")
        if st.button("Load Sample Sales Data"):
            sample_data = generate_sample_data()
            st.session_state.uploaded_data = sample_data
            st.success("Sample data loaded!")
    
    # Main Content Area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Data Upload Section
        st.markdown('<div class="section-header">📁 Data Upload</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'json'],
            help="Upload your dataset in CSV, Excel, or JSON format"
        )
        
        # Data Preview
        if uploaded_file is not None or st.session_state.uploaded_data is not None:
            if uploaded_file is not None:
                try:
                    # Load data based on file type
                    if uploaded_file.name.endswith('.csv'):
                        data = pd.read_csv(uploaded_file)
                    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                        data = pd.read_excel(uploaded_file)
                    elif uploaded_file.name.endswith('.json'):
                        data = pd.read_json(uploaded_file)
                    
                    st.session_state.uploaded_data = data
                    
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
                    return
            
            data = st.session_state.uploaded_data
            
            # Data Preview
            st.markdown('<div class="section-header">👀 Data Preview</div>', unsafe_allow_html=True)
            
            # Data info metrics
            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
            with col_metrics1:
                st.metric("Rows", f"{data.shape[0]:,}")
            with col_metrics2:
                st.metric("Columns", data.shape[1])
            with col_metrics3:
                st.metric("Missing Values", f"{data.isnull().sum().sum():,}")
            with col_metrics4:
                st.metric("Memory Usage", f"{data.memory_usage(deep=True).sum() / 1024:.1f} KB")
            
            # Show data preview
            st.dataframe(data.head(10), use_container_width=True)
            
            # Data types and basic info
            with st.expander("📋 Dataset Information"):
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("**Data Types:**")
                    dtype_df = pd.DataFrame({
                        'Column': data.dtypes.index,
                        'Type': data.dtypes.values
                    })
                    st.dataframe(dtype_df, hide_index=True)
                
                with col_info2:
                    st.markdown("**Missing Values:**")
                    missing_df = pd.DataFrame({
                        'Column': data.columns,
                        'Missing': data.isnull().sum().values,
                        'Percentage': (data.isnull().sum() / len(data) * 100).round(2)
                    })
                    missing_df = missing_df[missing_df['Missing'] > 0]
                    if not missing_df.empty:
                        st.dataframe(missing_df, hide_index=True)
                    else:
                        st.success("No missing values found!")
    
    with col2:
        # Quick Data Visualization
        if st.session_state.uploaded_data is not None:
            st.markdown('<div class="section-header">📊 Quick Insights</div>', unsafe_allow_html=True)
            
            data = st.session_state.uploaded_data
            
            # Numeric columns summary
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                selected_col = st.selectbox("Select column for quick viz:", numeric_cols)
                
                # Create simple histogram
                fig = px.histogram(data, x=selected_col, title=f"Distribution of {selected_col}")
                st.plotly_chart(fig, use_container_width=True)
            
            # Show basic statistics
            if len(numeric_cols) > 0:
                st.markdown("**Summary Statistics:**")
                st.dataframe(data[numeric_cols].describe(), use_container_width=True)
    
    # Analysis Section
    if st.session_state.uploaded_data is not None:
        st.markdown('<div class="section-header">🔍 Analysis Configuration</div>', unsafe_allow_html=True)
        
        col_analysis1, col_analysis2 = st.columns([2, 1])
        
        with col_analysis1:
            analysis_question = st.text_area(
                "What would you like to analyze?",
                placeholder="e.g., What are the key trends in sales performance? How do customer segments differ?",
                height=100
            )
            
            analysis_context = st.text_input(
                "Additional Context (Optional)",
                placeholder="e.g., This is quarterly sales data for business review"
            )
        
        with col_analysis2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Exploratory", "Descriptive", "Diagnostic", "Predictive"]
            )
            
            # Run Analysis Button
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                if not analysis_question.strip():
                    st.warning("Please enter an analysis question!")
                else:
                    run_analysis(data, analysis_question, analysis_context, azure_endpoint, azure_api_key)
    
    # Results Section
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        display_results()

def generate_sample_data():
    """Generate sample sales data for demonstration"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=300, freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(5000, 1000, 300) + np.sin(np.arange(300) * 2 * np.pi / 30) * 500,
        'region': np.random.choice(['North', 'South', 'East', 'West'], 300),
        'product_category': np.random.choice(['Electronics', 'Clothing', 'Home & Garden'], 300),
        'customer_satisfaction': np.random.uniform(3.0, 5.0, 300),
        'marketing_spend': np.random.normal(2000, 500, 300),
        'units_sold': np.random.poisson(50, 300)
    })
    
    # Add some trends
    data['sales'] = data['sales'] + np.where(data['region'] == 'North', 1000, 0)
    data['customer_satisfaction'] = np.clip(data['customer_satisfaction'], 1, 5)
    
    return data

def run_analysis(data, question, context, endpoint, api_key):
    """Run the analysis using the Data Analyzer Bot"""
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def analyze():
        try:
            # Initialize bot (using mock for demo)
            # bot = DataAnalyzerBot(endpoint, api_key)  # Use actual bot
            bot = MockDataAnalyzerBot()  # Using mock for demo
            
            # Update progress
            status_text.text("🔍 Running data analysis...")
            progress_bar.progress(25)
            
            # Run analysis
            results = await bot.analyze_data(data, question, context)
            
            progress_bar.progress(75)
            status_text.text("📝 Generating report...")
            
            # Generate report
            report = bot.generate_report(results)
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
            # Store results
            st.session_state.analysis_results = {
                'results': results,
                'report': report,
                'timestamp': datetime.now()
            }
            st.session_state.analysis_complete = True
            
            # Clear progress indicators
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            st.success("Analysis completed successfully!")
            st.rerun()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Analysis failed: {str(e)}")
    
    # Run async analysis
    asyncio.run(analyze())

def display_results():
    """Display analysis results"""
    
    st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
    
    results = st.session_state.analysis_results['results']
    
    # Results tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Analysis", "📖 Story", "📊 Visualizations", "📄 Full Report"])
    
    with tab1:
        st.markdown("### Key Insights")
        for i, insight in enumerate(results['analysis'].insights, 1):
            st.markdown(f'<div class="insight-box"><strong>{i}.</strong> {insight}</div>', unsafe_allow_html=True)
        
        st.markdown("### Detailed Analysis")
        st.markdown(results['analysis'].content)
        
        # Confidence score
        st.metric("Analysis Confidence", f"{results['analysis'].confidence_score:.1%}")
    
    with tab2:
        st.markdown("### Data Story")
        st.markdown(results['story'].content)
        
        st.markdown("### Story Insights")
        for insight in results['story'].insights:
            st.info(insight)
        
        st.metric("Story Confidence", f"{results['story'].confidence_score:.1%}")
    
    with tab3:
        st.markdown("### Visualization Recommendations")
        st.markdown(results['visualizations'].content)
        
        st.markdown("### Recommended Charts")
        for i, rec in enumerate(results['visualizations'].recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
        
        # Generate some sample visualizations based on the data
        if st.session_state.uploaded_data is not None:
            create_sample_visualizations(st.session_state.uploaded_data)
    
    with tab4:
        st.markdown("### Complete Analysis Report")
        st.markdown(st.session_state.analysis_results['report'])
        
        # Download button
        report_bytes = st.session_state.analysis_results['report'].encode()
        st.download_button(
            label="📥 Download Report",
            data=report_bytes,
            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )

def create_sample_visualizations(data):
    """Create sample visualizations based on data"""
    
    st.markdown("### Sample Visualizations")
    
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    categorical_cols = data.select_dtypes(include=['object']).columns
    
    if len(numeric_cols) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Correlation heatmap
            if len(numeric_cols) > 2:
                corr_matrix = data[numeric_cols].corr()
                fig = px.imshow(corr_matrix, text_auto=True, title="Correlation Heatmap")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Scatter plot
            if len(numeric_cols) >= 2:
                fig = px.scatter(
                    data, 
                    x=numeric_cols[0], 
                    y=numeric_cols[1],
                    title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Time series if date column exists
    date_cols = data.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0 and len(numeric_cols) > 0:
        fig = px.line(
            data, 
            x=date_cols[0], 
            y=numeric_cols[0],
            title=f"{numeric_cols[0]} Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()