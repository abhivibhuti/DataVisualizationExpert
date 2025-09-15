from openai import OpenAI

class DataAnalyzer:
    """
    An agent that analyzes data using an AI model.
    """
    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo-preview"):
        self.client = client
        self.model = model
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self):
        """Loads the prompt template from the file."""
        try:
            with open("prompts/data_analyzer_prompt.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            print("Error: prompts/data_analyzer_prompt.txt not found.")
            return None

    def analyze(self, data_string: str, brd_context: str = "Not provided.", user_question: str = "Not provided.") -> str:
        """
        Analyzes the given data string using the AI model, with additional context.

        Args:
            data_string: The data to be analyzed, as a string.
            brd_context: The content of the Business Requirements Document.
            user_question: A specific question from the user.

        Returns:
            The analysis report from the AI model.
        """
        if not self.prompt_template:
            return "Error: Prompt template not loaded."

        # Format the prompt with the data and additional context
        prompt = self.prompt_template.format(
            data=data_string,
            brd_context=brd_context,
            user_question=user_question
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during API call: {e}"
