from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.logging import logger
class QueryCategorizer:
    """ query categorization with better keyword detection"""
    def __init__(self, llm):
        self.llm = llm
        self.categorization_prompt = ChatPromptTemplate.from_template("""
        Analyze the user's query to determine its primary intent and categorize it into exactly ONE of the following categories.
        Focus on the most specific category that applies. For instance, questions about the rules of "Industrial Training" courses (like MEES281) belong in 'training_rules', not 'courses_and_curriculum'.
        Respond with ONLY the category name.

        ---
        ## Categories & Examples:
        - **courses_and_curriculum**: "What is the description of MDPS241?", "prereq for Control Systems"
        - **general_info**: "What is the program's vision?", "How many elective courses are there?"
        - **training_rules**: "Can my industrial training be online?", "How do I register for IT2?"
        - **results_statistics**: "Show me the grades for Thermodynamics in Fall 2024."
        ---
        Query: {query}
        Category:""")
        self.chain = self.categorization_prompt | self.llm | StrOutputParser()

    def categorize(self, query: str) -> str:
        #  keyword check
        query_lower = query.lower()
        if any(word in query_lower for word in ['grade', 'gpa', 'statistics', 'result', 'performance']):
            return "results_statistics"
        if any(word in query_lower for word in ['training', 'internship', 'it1', 'it2', 'industrial']):
            return "training_rules"
        if any(word in query_lower for word in ['prerequisite', 'prereq', 'description', 'course content']):
            return "courses_and_curriculum"
        
        # Fallback to LLM
        try:
            category = self.chain.invoke({"query": query}).strip().lower()
            valid_categories = ["courses_and_curriculum", "general_info", "training_rules", "results_statistics"]
            return category if category in valid_categories else "courses_and_curriculum"
        except Exception as e:
            logger.error(f"Categorization error: {e}")
            return "courses_and_curriculum"
