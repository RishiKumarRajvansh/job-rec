import os
import re
import PyPDF2
import docx2txt
from nlp_utils import extract_skills_from_text

def parse_resume(file_path, nlp_model, skill_keywords):
    """
    Parse resume file and extract text and skills.
    
    Args:
        file_path (str): Path to the resume file
        nlp_model: spaCy NLP model
        skill_keywords (list): List of skill keywords to look for
        
    Returns:
        tuple: (extracted_text, extracted_skills)
    """
    try:
        # Extract text based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            extracted_text = extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Extract skills from the text
        extracted_skills = extract_skills_from_text(extracted_text, nlp_model, skill_keywords)
        
        return extracted_text, extracted_skills
        
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return "", []

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    
    return clean_text(text)

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file."""
    try:
        text = docx2txt.process(docx_path)
        return clean_text(text)
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_txt(txt_path):
    """Extract text from TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return clean_text(text)
    except Exception as e:
        print(f"Error extracting text from TXT: {e}")
        return ""

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return ""
    
    # Replace multiple newlines with a single one
    text = re.sub(r'\n+', '\n', text)
    
    # Replace multiple spaces with a single one
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
