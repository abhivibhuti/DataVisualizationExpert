import argparse
import os
from openai import OpenAI
from dotenv import load_dotenv

# Agent imports
from agents.data_analyzer import DataAnalyzer

def load_data_as_string(file_path):
    """Loads data from a CSV file and returns it as a string."""
    if not file_path.endswith('.csv'):
        raise ValueError("Unsupported file format. Please use a CSV file.")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

def main():
    """Main function to orchestrate the agentic flow."""
    # Load environment variables from .env file
    load_dotenv()

    # Set up argument parser
    parser = argparse.ArgumentParser(description="AI-Powered Data Analysis and Reporting Agent")
    parser.add_argument("--file_path", required=True, help="Path to the data file (CSV only)")
    args = parser.parse_args()

    # Load the data
    try:
        data_string = load_data_as_string(args.file_path)
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please create a .env file and add your OpenAI API key.")
        return

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return

    print("OpenAI client initialized.")

    # --- Agent Orchestration ---
    print("\n--- Starting Agentic Flow ---")

    # 1. Data Analysis Agent
    print("\n1. Running Data Analysis Agent...")
    data_analysis_agent = DataAnalyzer(client)
    # Note: The CLI does not support BRD/user prompt context, only the Streamlit app does.
    analysis_report = data_analysis_agent.analyze(data_string)
    print("\n--- Data Analysis Report ---")
    print(analysis_report)
    print("----------------------------\n")


    # 2. Data Storytelling Agent (to be implemented)
    print("\n2. Running Data Storytelling Agent...")
    # ...
    print("   (Data Storytelling Agent not yet implemented)")


    # 3. Visualization Suggester Agent (to be implemented)
    print("\n3. Running Visualization Suggester Agent...")
    # ...
    print("   (Visualization Suggester Agent not yet implemented)")


    # 4. Power BI Guide Agent (to be implemented)
    print("\n4. Running Power BI Guide Agent...")
    # ...
    print("   (Power BI Guide Agent not yet implemented)")


    print("\n--- Agentic Flow Complete ---")


if __name__ == "__main__":
    main()
