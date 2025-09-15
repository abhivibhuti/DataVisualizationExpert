# AI-Powered Data Analysis and Reporting Agent

This project is an intelligent agentic flow that automates the process of data analysis, visualization, and reporting. It takes a dataset in CSV format, performs a detailed analysis, generates actionable insights, creates data stories, suggests visualizations, and provides a step-by-step guide to build a dashboard in Power BI.

*Note: To ensure compatibility with free deployment platforms, this application currently supports **CSV files only**.*

## Features

*   **Automated Data Analysis:** Get a comprehensive analysis of your data, including key metrics, trends, and anomalies.
*   **Data Storytelling:** Transform raw data into compelling narratives that explain business performance.
*   **Visualization Suggestions:** Receive recommendations for the best chart types to represent your data.
*   **Power BI Integration:** Generate a step-by-step guide to create a Power BI dashboard from your data.
*   **Documentation Generation:** Automatically create BRD, FRD, and SRS documents.

## Project Structure

```
.
├── agents/                 # Contains the different agents for specific tasks
├── data/                   # To store sample or user-uploaded data
├── prompts/                # Stores prompts for the AI models
├── templates/              # For document templates (BRD, FRD, etc.)
├── main.py                 # Main script to orchestrate the agentic flow
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your OpenAI API key:**
    Create a `.env` file in the root of the project and add your OpenAI API key:
    ```
    OPENAI_API_KEY='your_api_key_here'
    ```

## Usage

This project has two primary interfaces: a web-based UI (recommended) and a command-line script.

### Web Application (Streamlit)

The web application provides an interactive interface for uploading files and viewing the analysis.

To run the web app, use the following command:
```bash
streamlit run app.py
```
This will open the application in your web browser.

### Command-Line Interface (CLI)

The CLI can be used for a quick analysis directly from your terminal.

Run the main script with the path to your data file:
```bash
python main.py --file_path data/sales_data.csv
```
The script will process the data and print the report to the console.
