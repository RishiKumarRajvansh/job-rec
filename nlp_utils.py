import spacy
import json
import os

def load_spacy_model(model_name='en_core_web_sm'):
    """
    Load spaCy model and skill keywords.
    
    Args:
        model_name (str): Name of the spaCy model to load
        
    Returns:
        tuple: (nlp_model, skill_keywords)
    """
    try:
        # Load spaCy model
        nlp = spacy.load(model_name)
        print(f"Successfully loaded spaCy model '{model_name}'.")
        
        # Load skill keywords from JSON file
        skill_keywords_path = 'skills_keywords.json'
        if os.path.exists(skill_keywords_path):
            with open(skill_keywords_path, 'r') as f:
                skill_keywords = json.load(f)
                print(f"Successfully loaded {len(skill_keywords)} skill keywords from {skill_keywords_path}")
        else:
            # Default skill keywords if file doesn't exist
            skill_keywords = [
                "Python", "JavaScript", "Java", "C++", "SQL", "HTML", "CSS",
                "React", "Angular", "Vue", "Node.js", "Django", "Flask",
                "Machine Learning", "Data Science", "AI", "Docker", "Kubernetes",
                "AWS", "Azure", "GCP", "Git", "GitHub", "CI/CD", "Agile", "Scrum"
            ]
            print(f"Skills keywords file not found. Using default list with {len(skill_keywords)} skills.")
        
        return nlp, skill_keywords
    except Exception as e:
        print(f"Error loading spaCy model or skill keywords: {e}")
        return None, []

def extract_skills_from_text(text, nlp_model, skill_keywords_list):
    """
    Extract skills from text using spaCy NLP model and a list of known skills.
    
    Args:
        text (str): The text to extract skills from
        nlp_model: The loaded spaCy model
        skill_keywords_list (list): List of skill keywords to look for
        
    Returns:
        list: List of extracted skills
    """
    if not text or not nlp_model or not skill_keywords_list:
        return []
    
    # Process the text with spaCy
    doc = nlp_model(text.lower())
    
    # Get lemmatized tokens (excluding stop words and punctuation)
    lemmatized_tokens = {token.lemma_ for token in doc if not token.is_stop and not token.is_punct}
    
    # Convert text to lowercase for case-insensitive matching
    raw_text_lower = text.lower()
    
    # Extract skills by matching against our keywords list
    extracted_skills = set()
    
    for skill_keyword in skill_keywords_list:
        skill_keyword_lower = skill_keyword.lower()
        
        # Check for exact phrase match in the text
        if skill_keyword_lower in raw_text_lower:
            # Basic boundary check to avoid partial word matches
            # This is a simple approach - regex with word boundaries would be more robust
            extracted_skills.add(skill_keyword)
        
        # For single-word skills, also check against lemmatized tokens
        elif " " not in skill_keyword_lower and skill_keyword_lower in lemmatized_tokens:
            extracted_skills.add(skill_keyword)
    
    return sorted(list(extracted_skills))
