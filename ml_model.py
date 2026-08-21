from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

def train_intent_classifier():
    # Training data stored as pairs (text, label) to guarantee 100% length alignment
    training_data = [
        # CODING
        ("write a python script", "CODING"),
        ("how to fix this bug in javascript", "CODING"),
        ("debug my c++ code", "CODING"),
        ("create a function to sort an array", "CODING"),
        ("html css template", "CODING"),
        ("api integration error", "CODING"),
        ("git merge conflict", "CODING"),
        ("sql query optimization", "CODING"),
        
        # DATA_SCIENCE
        ("machine learning model", "DATA_SCIENCE"),
        ("pandas dataframe groupby", "DATA_SCIENCE"),
        ("train a linear regression", "DATA_SCIENCE"),
        ("data analysis with python", "DATA_SCIENCE"),
        ("calculate mean and standard deviation", "DATA_SCIENCE"),
        ("matplotlib plot scatter", "DATA_SCIENCE"),
        ("scikit-learn pipeline", "DATA_SCIENCE"),
        ("deep learning neural network", "DATA_SCIENCE"),
        
        # EXAM_PREP
        ("prepare notes for my exam", "EXAM_PREP"),
        ("create a study guide", "EXAM_PREP"),
        ("summarize this chapter for a test", "EXAM_PREP"),
        ("important questions for semester exam", "EXAM_PREP"),
        ("revise chemistry formulas", "EXAM_PREP"),
        ("physics derivation revision", "EXAM_PREP"),
        ("exam schedule plan", "EXAM_PREP"),
        ("key definitions to memorize", "EXAM_PREP"),
        
        # RESUME_ROASTER
        ("review my resume", "RESUME_ROASTER"),
        ("improve my cv", "RESUME_ROASTER"),
        ("critique my work experience bullet points", "RESUME_ROASTER"),
        ("is my resume ATS friendly", "RESUME_ROASTER"),
        ("make my resume sound more professional", "RESUME_ROASTER"),
        ("cover letter feedback", "RESUME_ROASTER"),
        ("optimize resume skills section", "RESUME_ROASTER"),
        
        # GENERAL
        ("hello", "GENERAL"),
        ("how are you", "GENERAL"),
        ("what is your name", "GENERAL"),
        ("tell me a joke", "GENERAL"),
        ("weather today", "GENERAL"),
        ("thanks", "GENERAL"),
        ("good morning", "GENERAL")
    ]
    
    # Safely unpack into X and y so lengths never mismatch
    X, y = zip(*training_data)
    
    model = make_pipeline(CountVectorizer(), MultinomialNB())
    model.fit(X, y)
    return model
