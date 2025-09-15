import streamlit as st
import csv
import io
from dotenv import load_dotenv
from openai import OpenAI
import os

# Import your agent
from agents.data_analyzer import DataAnalyzer

def load_csv_as_string(uploaded_file):
    """Loads data from an uploaded CSV file and returns it as a string."""
    try:
        # Read the uploaded file as a string
        string_data = uploaded_file.getvalue().decode('utf-8')
        # Basic validation: Check if it's valid CSV by trying to read it
        csv_reader = csv.reader(io.StringIO(string_data))
        # Reconstruct the string to ensure it's a clean CSV format
        string_io = io.StringIO()
        csv_writer = csv.writer(string_io)
        for row in csv_reader:
            csv_writer.writerow(row)
        return string_io.getvalue()
    except Exception as e:
        st.error(f"Failed to read or process CSV file: {e}")
        return None

def main():
    """
    The main function that runs the Streamlit application.
    """
    st.set_page_config(page_title="AI-Powered Data Analysis", layout="wide")
    load_dotenv()

    st.title("AI-Powered Data Analysis and Reporting Agent")

    st.write("""
    Upload your dataset and Business Requirements Document (BRD) to get started.
    The agent will analyze your data and provide insights.
    """)

    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("1. Upload Your Files")

        # Updated file uploader to only accept CSV
        uploaded_dataset = st.file_uploader("Upload your dataset (CSV only)", type=['csv'])

        uploaded_brd = st.file_uploader("Upload your BRD (optional, .txt or .md)", type=['txt', 'md'])

        st.header("2. Ask a Question")
        user_prompt = st.text_area("Ask a specific question about your data (optional)")

        st.header("3. Generate Analysis")
        analyze_button = st.button("Analyze Data")

    # --- Main Panel for Output ---
    tab1, tab2 = st.tabs(["Analysis Report", "FRD Generation"])

    with tab1:
        st.header("Analysis Report")
        if "analysis_report" not in st.session_state:
            st.session_state.analysis_report = None

        if analyze_button:
            if uploaded_dataset is not None:
                with st.spinner("Analysis in progress... Please wait."):
                    try:
                        # 1. Load data and context
                        data_string = load_csv_as_string(uploaded_dataset)

                        if data_string:
                            brd_content = "Not provided."
                            if uploaded_brd is not None:
                                brd_content = uploaded_brd.read().decode("utf-8")

                            # 2. Initialize OpenAI client and agent
                            api_key = os.getenv("OPENAI_API_KEY")
                            if not api_key:
                                st.error("Error: OPENAI_API_KEY not set. Please create a .env file.")
                                return

                            client = OpenAI(api_key=api_key)
                            data_analyzer = DataAnalyzer(client)

                            # 3. Run the analysis and store it in session state
                            st.session_state.analysis_report = data_analyzer.analyze(
                                data_string=data_string,
                                brd_context=brd_content,
                                user_question=user_prompt if user_prompt else "Not provided."
                            )
                        else:
                            # Error handled in load_csv_as_string
                            st.session_state.analysis_report = None

                    except Exception as e:
                        st.error(f"An error occurred during analysis: {e}")
                        st.session_state.analysis_report = None
            else:
                st.warning("Please upload a dataset to begin the analysis.")

        if st.session_state.analysis_report:
            st.markdown(st.session_state.analysis_report)

    with tab2:
        st.header("Functional Requirements Document (FRD)")
        st.write("This section will generate the FRD based on the uploaded BRD.")
        st.info("FRD generation logic will be implemented once the template is provided.")

        if st.button("Generate FRD"):
            st.warning("FRD generation is not yet implemented.")

if __name__ == "__main__":
    main()
