import os
import re
import PyPDF2
import docx
import docx2txt
import spacy
# from fuzzywuzzy import fuzz # Not used in the current nlp_utils.py
# from nlp_utils import extract_skills_from_text # Redundant, using the provided nlp_utils.py
from nlp_utils import extract_skills_from_text, extract_location_from_text


def parse_resume(file_path, nlp_model, skill_keywords=None):
    """
    Parse resume file and extract text, skills, and location.

    Args:
        file_path (str): Path to the resume file
        nlp_model: spaCy NLP model
        skill_keywords (list): List of skill keywords to look for (not used in current nlp_utils)

    Returns:
        tuple: (extracted_text, extracted_skills, extracted_location)
    """
    extracted_text = ""
    extracted_skills = []
    extracted_location = ""
    try:
        print(f"Starting resume parsing for file: {file_path}")

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

        extracted_text = clean_text(extracted_text)

        print(f"Extracted text length: {len(extracted_text)}")
        if len(extracted_text) < 100:
            print(f"Warning: Very short text extracted: {extracted_text}")

        # Extract skills from the text
        extracted_skills = extract_skills_from_text(extracted_text, nlp_model, skill_keywords)
        print(f"Extracted {len(extracted_skills)} skills from resume")

        # Extract location from the text
        extracted_location = extract_location_from_text(extracted_text, nlp_model)
        print(f"Extracted location: {extracted_location}")

        return extracted_text, extracted_skills, extracted_location

    except Exception as e:
        import traceback

        print(f"Error parsing resume: {e}")
        print(traceback.format_exc())
        return extracted_text, extracted_skills, extracted_location


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"

        print(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        print(f"Extracted {len(text)} characters from DOCX")
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return text


def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        print(f"Extracted {len(text)} characters from TXT")
        return text
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()

            print(f"Extracted {len(text)} characters from TXT (latin-1 encoding)")
            return text
        except Exception as e:
            print(f"Error extracting text from TXT with latin-1 encoding: {e}")
            return text
    except Exception as e:
        print(f"Error extracting text from TXT: {e}")
        return text


# def extract_location_from_text(text, nlp_model): # Removed, using the provided nlp_utils.py
#     """Extract location from text using NLP and regex"""
#     locations = []

#     # 1. spaCy NER
#     doc = nlp_model(text)
#     locations.extend([ent.text for ent in doc.ents if ent.label_ == "GPE"])

#     # 2. Regular Expressions
#     location_patterns = [
#         r"(?i)([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*),\s*(?:[A-Z]{2}|[A-Z][a-z]+)",  # City, State
#         r"(?i)(?:Address|Location|City|Town|State|Country|Region)\s*:\s*([^\n,]+)",
#     ]
#     for pattern in location_patterns:
#         locations.extend(re.findall(pattern, text))

#     # 3. Clean and Deduplicate
#     unique_locations = []
#     for loc in locations:
#         loc = loc.strip()
#         if loc and loc not in unique_locations:
#             unique_locations.append(loc)

#     # 4. Return the first location found (you can implement a scoring mechanism here)
#     return unique_locations[0] if unique_locations else ""

def extract_skills_from_text(text, nlp_model, skill_keywords=None):
    """
    Extract skills from text using NLP with a focus on identifying the skills section.
    This function no longer uses the skill_keywords parameter for extraction,
    relying solely on NLP and pattern matching within the text.
    Args:
        text (str): Text to extract skills from
        nlp_model: spaCy NLP model
        skill_keywords (list): This parameter is ignored in this version.
    Returns:
        list: List of extracted skills
    """
    print("Starting skill extraction...")
    if not text or not nlp_model:
        print("No text or NLP model provided")
        return []

    # First, try to identify the skills section in the resume
    # Common section headers for skills
    skill_section_patterns = [
        r'(?:technical\s+)?skills(?:\s+and\s+competencies)?(?:\s*:|\s*\n)',
        r'(?:technical|professional)\s+(?:skills|proficiencies)(?:\s*:|\s*\n)',
        r'(?:core\s+)?competencies(?:\s*:|\s*\n)',
        r'(?:technical|professional)\s+(?:qualifications|expertise)(?:\s*:|\s*\n)',
        r'technologies(?:\s*:|\s*\n)',
        r'technical\s+background(?:\s*:|\s*\n)',
        r'skill\s+set(?:\s*:|\s*\n)',
        r'areas\s+of\s+expertise(?:\s*:|\s*\n)',
        r'technical\s+knowledge(?:\s*:|\s*\n)',
        r'programming\s+(?:languages|skills)(?:\s*:|\s*\n)',
        r'software\s+(?:proficiencies|skills)(?:\s*:|\s*\n)',
        r'tools\s+(?:and\s+technologies|&\s+technologies)(?:\s*:|\s*\n)',
    ]
    # Try to find the skills section
    skills_section_text = None
    next_section_start = None
    # Add a marker to the end to ensure the last section is captured if no next header exists
    text_with_end_marker = text + "\nEND_OF_DOCUMENT_MARKER"
    for pattern in skill_section_patterns:
        matches = list(re.finditer(pattern, text_with_end_marker, re.IGNORECASE))
        if matches:
            # Found a skills section header
            section_start = matches[0].end() # Use .end() to start after the header
            # Look for the next section header to determine where skills section ends
            # Common section headers that might follow skills
            next_section_patterns = [
                r'education(?:\s*:|\s*\n)',
                r'experience(?:\s*:|\s*\n)',
                r'employment(?:\s+history)?(?:\s*:|\s*\n)',
                r'work(?:\s+history)?(?:\s*:|\s*\n)',
                r'projects(?:\s*:|\s*\n)',
                r'certifications(?:\s*:|\s*\n)',
                r'awards(?:\s*:|\s*\n)',
                r'publications(?:\s*:|\s*\n)',
                r'languages(?:\s*:|\s*\n)', # Note: 'languages' can be a skill category, but also a section header
                r'interests(?:\s*:|\s*\n)',
                r'references(?:\s*:|\s*\n)',
                r'additional\s+information(?:\s*:|\s*\n)',
                r'END_OF_DOCUMENT_MARKER', # Use the marker as a potential end
            ]
            # Find all potential next sections *after* the current section start
            potential_next_sections = []
            for next_pattern in next_section_patterns:
               # Search only in the text *after* the current section header
               next_matches = list(re.finditer(next_pattern, text_with_end_marker[section_start:], re.IGNORECASE))
               if next_matches:
                   # Add the start position relative to the original text
                   potential_next_sections.append(section_start + next_matches[0].start())
            # If we found potential next sections, use the closest one
            if potential_next_sections:
                next_section_start = min(potential_next_sections)
                skills_section_text = text_with_end_marker[section_start:next_section_start].strip()
            else:
                # If no next section found, use the rest of the text
                skills_section_text = text_with_end_marker[section_start:].strip()
            print(f"Found skills section starting after '{matches[0].group(0).strip()}': {len(skills_section_text)} characters")
            break # Stop after finding the first skills section

    # If we couldn't identify a specific skills section, use the whole text
    if not skills_section_text:
        print("Could not identify a specific skills section, using whole text")
        skills_section_text = text

    extracted_skills = set()
    # Extract skills using bullet points and list patterns
    print("Extracting skills from bullet points and lists...")
    bullet_patterns = [
        r'(?:^|\n)[\s•\-*]+([^•\-*\n]+)',  # Bullet points at start of line
        r'(?:^|\n)[\d]+\.[\s]+([^\n]+)',   # Numbered lists
    ]
    for pattern in bullet_patterns:
        matches = re.finditer(pattern, skills_section_text, re.MULTILINE)
        for match in matches:
            skill_text = match.group(1).strip()
            # Check if this looks like a skill (not too long, not too short)
            if 2 <= len(skill_text) <= 50:
                # Split by common delimiters within a list item
                delimiters = r'[,;]\s*|\s+and\s+'
                skills_in_item = re.split(delimiters, skill_text, flags=re.IGNORECASE)
                for skill in skills_in_item:
                    skill = skill.strip()
                    # Further refine: remove trailing punctuation, check length
                    skill = re.sub(r'[.,;:]+$', '', skill)
                    if skill and len(skill) > 1: # Avoid single characters or empty strings
                        extracted_skills.add(skill)

    # Look for skills in colon-separated lists (e.g., "Skills: Python, Java, SQL")
    print("Extracting skills from colon-separated lists...")
    colon_list_patterns = [
        r'(?i)(?:Skills|Technologies|Tools|Proficiencies|Expertise|Languages)\s*:\s*(.+)',
    ]
    for pattern in colon_list_patterns:
        match = re.search(pattern, skills_section_text)
        if match:
            list_text = match.group(1).strip()
            # Split the list text by commas, semicolons, or "and"
            skills_in_list = re.split(r'[,;]\s*|\s+and\s+', list_text, flags=re.IGNORECASE)
            for skill in skills_in_list:
                skill = skill.strip()
                # Further refine: remove trailing punctuation, check length
                skill = re.sub(r'[.,;:]+$', '', skill)
                if skill and len(skill) > 1:
                    extracted_skills.add(skill)

    # --- Additional NLP-based extraction (can be noisy) ---
    # Process the skills section text with spaCy for potential entities or noun chunks
    print("Performing additional NLP extraction...")
    doc_skills_section = nlp_model(skills_section_text)
    # Look for proper nouns (NNP) or noun chunks that might be skills
    # This can be very noisy and requires careful filtering
    potential_skills_nlp = set()
    for chunk in doc_skills_section.noun_chunks:
        chunk_text = chunk.text.strip()
        # Filter out common non-skill phrases or short chunks
        if len(chunk_text.split()) <= 4 and len(chunk_text) > 2 and chunk_text.lower() not in ["experience", "education", "projects", "summary", "technologies", "skills", "proficiencies", "competencies", "qualifications", "expertise", "background", "set", "areas", "knowledge", "languages", "software", "tools", "information", "history"]:
            potential_skills_nlp.add(chunk_text)

    # Add potential NLP skills, but be cautious
    # A more advanced approach would involve checking these against a known list or using a custom NER model
    # For now, we'll add them but they might include noise.
    # Consider adding only if they contain at least one capitalized word (heuristic for proper nouns/tech names)
    # Or if they look like common tech terms (e.g., contain '.', '-', '#', '+')
    for skill in potential_skills_nlp:
        if any(char in skill for char in ['.', '-', '#', '+']) or any(word.isupper() or (len(word) > 1 and word[0].isupper()) for word in skill.split()):
            extracted_skills.add(skill)

    # Clean and format the final list
    final_skills = sorted(list(extracted_skills))
    print(f"Finished skill extraction. Found {len(final_skills)} skills.")
    return final_skills

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return ""

    # Replace multiple newlines with a single one
    text = re.sub(r'\n+', '\n', text)

    # Replace multiple spaces with a single one
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
