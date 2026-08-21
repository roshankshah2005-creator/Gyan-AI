from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

def train_intent_classifier():
    """Trains and returns an expanded Scikit-Learn pipeline for high-confidence intent classification."""
    X_train = [
        # CODING
        "How do I write a python function?", "Debug my code", "SQL query syntax error", 
        "Fix this bug", "How to use arrays in javascript", "Write a loop in c++",
        "How to create a REST API", "TypeError in python", "Git commit error",
        
        # DATA SCIENCE
        "Explain linear regression", "Data science roadmap", "Pandas dataframe merge technique", 
        "Train a random forest model", "Handle missing values in dataset", "What is feature scaling",
        "Calculate mean squared error", "K-means clustering algorithm", "Matplotlib visualization",
        # EXAM_PREP
        "prepare notes for my exam", "create a study guide", "summarize this chapter for a test", "important questions for semester exam",
        "revise chemistry formulas", "physics derivation revision", "exam schedule plan", "key definitions to memorize",
        # RESUME_ROASTER
        "review my resume", "improve my cv", "critique my work experience bullet points", "is my resume ATS friendly",
        "make my resume sound more professional", "cover letter feedback", "optimize resume skills section",
        # GENERAL
        "What is the schedule?", "Hello", "How are you doing today?", "Tell me a joke", 
        "What can you do?", "Who made you?", "Good morning", "Thanks for the help"
    ]
    
    y_train = [
        "CODING", "CODING", "CODING", "CODING", "CODING", "CODING", "CODING", "CODING",
        "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE", "DATA_SCIENCE",
        "EXAM_PREP", "EXAM_PREP", "EXAM_PREP", "EXAM_PREP", "EXAM_PREP", "EXAM_PREP", "EXAM_PREP", "EXAM_PREP",
        "RESUME_ROASTER", "RESUME_ROASTER", "RESUME_ROASTER", "RESUME_ROASTER", "RESUME_ROASTER", "RESUME_ROASTER", "RESUME_ROASTER",
        "GENERAL", "GENERAL", "GENERAL", "GENERAL", "GENERAL", "GENERAL", "GENERAL"
    ]
    model = make_pipeline(CountVectorizer(), MultinomialNB())
    model.fit(X_train, y_train)
    return model