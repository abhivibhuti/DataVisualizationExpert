import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from openai import AsyncAzureOpenAI
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import base64

class AgentType(Enum):
    DATA_ANALYST = "data_analyst"
    STORYTELLER = "storyteller"
    VISUALIZATION_SUGGESTER = "visualization_suggester"

@dataclass
class AnalysisRequest:
    data: pd.DataFrame
    question: str
    context: Optional[str] = None
    analysis_type: Optional[str] = "exploratory"

@dataclass
class AgentResponse:
    agent_type: AgentType
    content: str
    insights: List[str]
    recommendations: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

class AzureOpenAIClient:
    """Azure OpenAI client wrapper for the data analysis agents"""
    
    def __init__(self, endpoint: str, api_key: str, api_version: str = "2024-02-15-preview"):
        self.client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
    
    async def generate_response(self, messages: List[Dict], model: str = "gpt-4", **kwargs):
        """Generate response from Azure OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                top_p=kwargs.get('top_p', 0.95)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

class DataAnalysisAgent:
    """Agent specialized in statistical data analysis"""
    
    def __init__(self, azure_client: AzureOpenAIClient):
        self.azure_client = azure_client
        self.agent_type = AgentType.DATA_ANALYST
        
    def _generate_data_summary(self, df: pd.DataFrame) -> str:
        """Generate comprehensive data summary"""
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {},
            "categorical_summary": {col: df[col].value_counts().head().to_dict() 
                                  for col in df.select_dtypes(include=['object']).columns}
        }
        return json.dumps(summary, indent=2, default=str)
    
    async def analyze(self, request: AnalysisRequest) -> AgentResponse:
        """Perform comprehensive data analysis"""
        data_summary = self._generate_data_summary(request.data)
        
        system_prompt = """You are an expert data analyst. Your role is to:
        1. Analyze the provided dataset comprehensively
        2. Identify patterns, trends, and anomalies
        3. Perform statistical analysis
        4. Generate actionable insights
        5. Suggest further analysis directions
        
        Focus on statistical significance, data quality issues, and business relevance."""
        
        user_prompt = f"""
        Please analyze the following dataset:
        
        Data Summary:
        {data_summary}
        
        User Question: {request.question}
        Context: {request.context or 'No additional context provided'}
        Analysis Type: {request.analysis_type}
        
        Provide:
        1. Key statistical insights
        2. Data quality assessment
        3. Pattern identification
        4. Anomaly detection
        5. Recommendations for further analysis
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_content = await self.azure_client.generate_response(messages)
        
        # Extract insights and recommendations (simplified parsing)
        insights = self._extract_insights(response_content)
        recommendations = self._extract_recommendations(response_content)
        
        return AgentResponse(
            agent_type=self.agent_type,
            content=response_content,
            insights=insights,
            recommendations=recommendations,
            confidence_score=0.85,  # Could be calculated based on data quality
            metadata={"data_shape": request.data.shape, "analysis_type": request.analysis_type}
        )
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract key insights from the analysis response"""
        # Simplified extraction - could be enhanced with NLP
        lines = content.split('\n')
        insights = []
        in_insights_section = False
        
        for line in lines:
            if 'insight' in line.lower() or 'finding' in line.lower():
                in_insights_section = True
            elif in_insights_section and line.strip():
                insights.append(line.strip())
        
        return insights[:5]  # Return top 5 insights
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from the analysis response"""
        lines = content.split('\n')
        recommendations = []
        in_recommendations_section = False
        
        for line in lines:
            if 'recommend' in line.lower() or 'suggest' in line.lower():
                in_recommendations_section = True
            elif in_recommendations_section and line.strip():
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Return top 5 recommendations

class DataStorytellingAgent:
    """Agent specialized in creating data narratives and stories"""
    
    def __init__(self, azure_client: AzureOpenAIClient):
        self.azure_client = azure_client
        self.agent_type = AgentType.STORYTELLER
    
    async def create_story(self, analysis_response: AgentResponse, request: AnalysisRequest) -> AgentResponse:
        """Create compelling data story from analysis results"""
        
        system_prompt = """You are an expert data storyteller. Your role is to:
        1. Transform analytical insights into compelling narratives
        2. Create engaging data stories that resonate with stakeholders
        3. Use storytelling frameworks (situation-complication-resolution)
        4. Make complex data accessible to non-technical audiences
        5. Provide actionable business narratives
        
        Focus on clarity, engagement, and business impact."""
        
        user_prompt = f"""
        Create a compelling data story based on the following analysis:
        
        Original Question: {request.question}
        Analysis Insights: {', '.join(analysis_response.insights)}
        Recommendations: {', '.join(analysis_response.recommendations)}
        Data Context: {request.context}
        
        Create a story that:
        1. Sets the business context
        2. Presents the data challenge/opportunity
        3. Reveals key insights through narrative
        4. Provides clear resolution/action items
        5. Uses analogies and metaphors where appropriate
        
        Target audience: Business stakeholders and decision makers
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_content = await self.azure_client.generate_response(messages)
        
        return AgentResponse(
            agent_type=self.agent_type,
            content=response_content,
            insights=self._extract_story_insights(response_content),
            recommendations=self._extract_story_recommendations(response_content),
            confidence_score=0.90,
            metadata={"story_type": "business_narrative", "target_audience": "stakeholders"}
        )
    
    def _extract_story_insights(self, content: str) -> List[str]:
        """Extract key story insights"""
        # Enhanced story-specific insight extraction
        insights = []
        lines = content.split('.')
        for line in lines:
            if any(word in line.lower() for word in ['reveals', 'shows', 'indicates', 'demonstrates']):
                insights.append(line.strip())
        return insights[:3]
    
    def _extract_story_recommendations(self, content: str) -> List[str]:
        """Extract story-based recommendations"""
        recommendations = []
        lines = content.split('.')
        for line in lines:
            if any(word in line.lower() for word in ['should', 'must', 'recommend', 'action']):
                recommendations.append(line.strip())
        return recommendations[:3]

class VisualizationSuggesterAgent:
    """Agent specialized in suggesting appropriate visualizations"""
    
    def __init__(self, azure_client: AzureOpenAIClient):
        self.azure_client = azure_client
        self.agent_type = AgentType.VISUALIZATION_SUGGESTER
    
    async def suggest_visualizations(self, request: AnalysisRequest, analysis_response: AgentResponse) -> AgentResponse:
        """Suggest appropriate visualizations for the data and analysis"""
        
        # Analyze data characteristics
        data_profile = self._profile_data(request.data)
        
        system_prompt = """You are an expert data visualization consultant. Your role is to:
        1. Recommend the most effective visualizations for specific data types and questions
        2. Consider the audience and purpose of visualizations
        3. Suggest both standard and advanced visualization techniques
        4. Provide specific implementation guidance
        5. Consider accessibility and best practices
        
        Focus on clarity, accuracy, and visual impact."""
        
        user_prompt = f"""
        Suggest visualizations for this analysis:
        
        Data Profile: {json.dumps(data_profile, indent=2)}
        User Question: {request.question}
        Key Insights: {', '.join(analysis_response.insights)}
        Analysis Type: {request.analysis_type}
        
        For each visualization suggestion, provide:
        1. Chart type and rationale
        2. Which variables to use (x, y, color, size, etc.)
        3. Best practices for implementation
        4. Alternative options
        5. Tools/libraries recommendations
        
        Consider both exploratory and presentation-ready visualizations.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_content = await self.azure_client.generate_response(messages)
        
        viz_suggestions = self._parse_visualization_suggestions(response_content)
        
        return AgentResponse(
            agent_type=self.agent_type,
            content=response_content,
            insights=viz_suggestions.get('insights', []),
            recommendations=viz_suggestions.get('chart_types', []),
            confidence_score=0.88,
            metadata={"data_profile": data_profile, "viz_count": len(viz_suggestions.get('chart_types', []))}
        )
    
    def _profile_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create data profile for visualization recommendations"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        return {
            "total_columns": len(df.columns),
            "total_rows": len(df),
            "numeric_columns": len(numeric_cols),
            "categorical_columns": len(categorical_cols),
            "datetime_columns": len(datetime_cols),
            "column_details": {
                "numeric": numeric_cols,
                "categorical": categorical_cols,
                "datetime": datetime_cols
            },
            "data_density": df.notna().sum().sum() / (df.shape[0] * df.shape[1])
        }
    
    def _parse_visualization_suggestions(self, content: str) -> Dict[str, List[str]]:
        """Parse visualization suggestions from response"""
        chart_types = []
        insights = []
        
        # Simplified parsing - could be enhanced with better NLP
        lines = content.split('\n')
        for line in lines:
            if any(chart in line.lower() for chart in ['bar', 'line', 'scatter', 'histogram', 'box', 'heatmap']):
                chart_types.append(line.strip())
            elif 'insight' in line.lower() or 'effective' in line.lower():
                insights.append(line.strip())
        
        return {"chart_types": chart_types, "insights": insights}

class DataAnalyzerBot:
    """Main orchestrator for the data analysis bot"""
    
    def __init__(self, azure_endpoint: str, azure_api_key: str):
        self.azure_client = AzureOpenAIClient(azure_endpoint, azure_api_key)
        self.data_analyst = DataAnalysisAgent(self.azure_client)
        self.storyteller = DataStorytellingAgent(self.azure_client)
        self.viz_suggester = VisualizationSuggesterAgent(self.azure_client)
    
    async def analyze_data(self, data: pd.DataFrame, question: str, context: str = None) -> Dict[str, AgentResponse]:
        """Run complete data analysis pipeline"""
        
        request = AnalysisRequest(data=data, question=question, context=context)
        
        # Step 1: Data Analysis
        print("🔍 Running data analysis...")
        analysis_response = await self.data_analyst.analyze(request)
        
        # Step 2: Create Data Story
        print("📖 Creating data story...")
        story_response = await self.storyteller.create_story(analysis_response, request)
        
        # Step 3: Suggest Visualizations
        print("📊 Suggesting visualizations...")
        viz_response = await self.viz_suggester.suggest_visualizations(request, analysis_response)
        
        return {
            "analysis": analysis_response,
            "story": story_response,
            "visualizations": viz_response
        }
    
    def generate_report(self, results: Dict[str, AgentResponse]) -> str:
        """Generate comprehensive analysis report"""
        
        report = f"""
# Data Analysis Report
Generated by Data Analyzer Bot

## Executive Summary
{results['story'].content[:500]}...

## Key Insights
"""
        
        for i, insight in enumerate(results['analysis'].insights, 1):
            report += f"{i}. {insight}\n"
        
        report += f"""
## Data Story
{results['story'].content}

## Visualization Recommendations
{results['visualizations'].content}

## Technical Analysis Details
{results['analysis'].content}

---
*Report generated with confidence scores: Analysis ({results['analysis'].confidence_score:.2f}), Story ({results['story'].confidence_score:.2f}), Visualizations ({results['visualizations'].confidence_score:.2f})*
"""
        
        return report

# Example usage and testing
async def main():
    """Example usage of the Data Analyzer Bot"""
    
    # Configuration (replace with your actual Azure OpenAI credentials)
    AZURE_ENDPOINT = "https://your-resource.openai.azure.com/"
    AZURE_API_KEY = "your-api-key"
    
    # Initialize the bot
    bot = DataAnalyzerBot(AZURE_ENDPOINT, AZURE_API_KEY)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'sales': np.random.normal(1000, 200, 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
        'product': np.random.choice(['A', 'B', 'C'], 100),
        'customer_satisfaction': np.random.uniform(3.0, 5.0, 100)
    })
    
    # Run analysis
    question = "What are the key trends in sales performance and how do they vary by region?"
    context = "This is sales data for our company's quarterly review"
    
    try:
        results = await bot.analyze_data(sample_data, question, context)
        
        # Generate and print report
        report = bot.generate_report(results)
        print(report)
        
        # Save report to file
        with open('data_analysis_report.md', 'w') as f:
            f.write(report)
        
        print("\n✅ Analysis complete! Report saved to 'data_analysis_report.md'")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

# Configuration helper
class ConfigurationHelper:
    """Helper class for setting up Azure OpenAI configuration"""
    
    @staticmethod
    def setup_environment():
        """Setup environment variables for Azure OpenAI"""
        print("""
To use this Data Analyzer Bot, you need to set up Azure OpenAI:

1. Create an Azure OpenAI resource in the Azure portal
2. Deploy a GPT-4 model (recommended: gpt-4 or gpt-4-32k)
3. Get your endpoint and API key from the Azure portal
4. Set the following environment variables:

export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"

Or update the credentials directly in the main() function.
        """)
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> List[str]:
        """Validate input data and return recommendations"""
        issues = []
        
        if df.empty:
            issues.append("DataFrame is empty")
        
        if df.shape[1] < 2:
            issues.append("Dataset should have at least 2 columns for meaningful analysis")
        
        if df.isnull().sum().sum() > df.shape[0] * df.shape[1] * 0.5:
            issues.append("Dataset has more than 50% missing values")
        
        return issues

if __name__ == "__main__":
    # Print setup instructions
    ConfigurationHelper.setup_environment()
    
    # Uncomment to run the example
    # asyncio.run(main())