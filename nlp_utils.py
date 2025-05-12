import json
import os
import re
import spacy
from spacy.matcher import PhraseMatcher
import string
import nltk
from nltk.corpus import stopwords

# Try to download NLTK stopwords if needed
try:
    nltk.data.find('corpora/stopwords')
except (LookupError, ImportError):
    try:
        nltk.download('stopwords', quiet=True)
    except:
        pass  # Continue even if we can't download stopwords

# Path to skills data file - we'll include this as a JSON string in the code
# instead of creating a separate file
SKILLS_JSON = '''{
  "skills": [
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "asp.net", "laravel",
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "cassandra", "dynamodb", "redis",
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "git", "github", "gitlab",
    "jira", "bitbucket", "html", "css", "sass", "less", "bootstrap", "tailwind", "jquery",
    "rest api", "graphql", "json", "xml", "soap", "microservices", "serverless", "linux", "unix", "bash",
    "powershell", "agile", "scrum", "kanban", "devops", "ci/cd", "data science", "machine learning", "ai",
    "tensorflow", "pytorch", "keras", "numpy", "pandas", "scikit-learn", "matplotlib", "hadoop", "spark",
    "elasticsearch", "kibana", "logstash", "tableau", "power bi", "excel", "vba", "etl", "data warehousing",
    "big data", "data mining", "data analysis", "statistics", "r", "matlab", "sas", "spss", "scala", "kafka",
    "rabbitmq", "activemq", "celery", "redis queue", "pytest", "junit", "nunit", "selenium", "cypress",
    "jest", "mocha", "chai", "webpack", "babel", "eslint", "prettier", "npm", "yarn", "pip", "conda",
    "virtualenv", "docker-compose", "vagrant", "ansible", "puppet", "chef", "nginx", "apache", "iis",
    "tomcat", "websphere", "weblogic", "oauth", "jwt", "saml", "ldap", "active directory", "wordpress",
    "drupal", "magento", "shopify", "woocommerce", "seo", "sem", "google analytics", "google tag manager",
    "ux", "ui", "photoshop", "illustrator", "sketch", "figma", "swift ui", "flutter", "react native", 
    "xamarin", "ionic", "cordova", "objective-c", "kotlin", "android sdk", "ios sdk", "xcode", 
    "android studio", "firebase", "realm", "coredata", "sqllite", "room", "mvvm", "mvc",
    "clean architecture", "design patterns", "solid principles", "tdd", "bdd", "ddd", "functional programming",
    "object-oriented programming", "reactive programming", "concurrency", "multithreading", "async/await",
    "blockchain", "cryptocurrency", "smart contracts", "solidity", "web3", "ethereum", "hyperledger",
    "networking", "tcp/ip", "http/https", "dns", "dhcp", "ftp", "ssh", "vpn", "load balancing", "proxy",
    "caching", "cdn", "websockets", "webrtc", "grpc", "amqp", "mqtt", "iot", "embedded systems", "raspberry pi",
    "arduino", "plc", "scada", "cybersecurity", "penetration testing", "vulnerability assessment", "encryption",
    "authentication", "authorization", "firewall", "ids/ips", "siem", "dlp", "cloud security", "devsecops",
    "js", "ts", "golang", "rust", "perl", "r", "shell", "nosql", "next.js", "nextjs", "nuxt", "rails", 
    "symfony", "material-ui", "chakra-ui", "ember", "backbone", "jetpack compose", "swiftui", "mariadb", 
    "neo4j", "couchdb", "supabase", "datomic", "k8s", "gitlab ci", "github actions", "puppet", "chef", 
    "vagrant", "prometheus", "grafana", "lambda", "serverless", "ec2", "s3", "eks", "ecs", "rds", "cloudfront",
    "continuous integration", "continuous deployment", "ml", "deep learning", "dl", "computer vision", 
    "natural language processing", "data studio", "looker", "predictive analytics", "responsive design",
    "jamstack", "redux", "mobx", "context api", "webgl", "canvas", "svg", "unit testing", "integration testing",
    "e2e testing", "testing library", "testng", "rspec", "cucumber", "jasmine", "cybersecurity", "infosec",
    "penetration testing", "pentest", "oauth", "jwt", "hashing", "ssl", "tls", "https", "joomla", "contentful",
    "strapi", "sanity", "netlify cms", "ghost", "soap", "grpc", "websocket", "blockchain", "ar", "vr",
    "embedded systems", "virtualization", "web services", "paas", "iaas", "distributed systems", "caching",
    "memcached", "cdn", "soa", "etl", "message queue", "service bus", "oauth", "openid", "saml", "system design"
  ]
}'''

# Common words that might be falsely identified as skills
SKILL_STOPWORDS = {
    'able', 'about', 'across', 'after', 'detail', 'team', 'building',
    'using', 'used', 'well', 'work', 'working', 'works', 'year', 'years',
    'skills', 'skill', 'proficient', 'experience', 'experienced', 'familiar',
    'knowledge', 'background', 'understanding', 'proficiency',
    'right', 'left', 'up', 'down', 'top', 'bottom', 'ms', 'etc', 'new', 'good',
    'part', 'better', 'best', 'lot', 'need', 'high', 'low'
}

def load_spacy_model(model_name="en_core_web_sm"):
    """
    Load the specified spaCy language model and return both the model and skill keywords.
    
    Args:
        model_name (str): Name of the spaCy model to load
        
    Returns:
        tuple: (spaCy language model, list of skill keywords)
    """
    try:
        nlp = spacy.load(model_name)
        print(f"Loaded spaCy model '{model_name}'")
    except OSError:
        print(f"spaCy model '{model_name}' not found. Downloading...")
        import subprocess
        subprocess.check_call([
            "python", "-m", "spacy", "download", model_name
        ])
        nlp = spacy.load(model_name)
        print(f"Successfully downloaded and loaded '{model_name}'")
    
    # Load skills data from the embedded JSON
    skills_data = json.loads(SKILLS_JSON)
    # Get just the skills list (no soft skills, software, certificates as requested)
    skill_keywords = skills_data["skills"]
    
    return nlp, skill_keywords

def extract_skills_from_text(text, nlp):
    """
    Extract technical skills from text using NLP and a predefined skills database.
    
    Args:
        text (str): The text to analyze
        nlp: spaCy loaded language model
        
    Returns:
        list: List of identified skills
    """
    if not text or not isinstance(text, str):
        return []
    
    # Load skills data from the embedded JSON
    skills_data = json.loads(SKILLS_JSON)
    
    # Get the technical skills list
    all_skills = skills_data["skills"]
    
    # Create phrase patterns for multi-word skills
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    # Separate single and multi-word skills
    single_word_skills = set()
    multi_word_skills = []
    
    for skill in all_skills:
        skill_lower = skill.lower().strip()
        if not skill_lower or len(skill_lower) < 2:
            continue
            
        if ' ' in skill_lower:
            multi_word_skills.append(skill_lower)
            pattern = nlp(skill_lower)
            skill_key = skill_lower.replace(' ', '_')
            matcher.add(skill_key, [pattern])
        else:
            single_word_skills.add(skill_lower)
    
    # Process the document with spaCy
    doc = nlp(text.lower())
    
    # Find all skill matches using the matcher for multi-word skills
    matches = matcher(doc)
    matched_skills = set()
    
    # Extract multi-word skills
    for match_id, start, end in matches:
        span = doc[start:end]
        skill_text = span.text.lower()
        if skill_text not in SKILL_STOPWORDS:
            matched_skills.add(skill_text)
    
    # Extract single-word skills
    for token in doc:
        token_text = token.text.lower()
        
        # Skip punctuation, stop words, etc.
        if (token.is_punct or token.is_stop or token.is_space or 
            len(token_text) < 2 or token_text in SKILL_STOPWORDS):
            continue
            
        # Check if the token is in our skills list
        if token_text in single_word_skills:
            # For very common terms that could be ambiguous, check context
            if token_text in ['c', 'r', 'go', 'js', 'us']:
                # Check if it appears to be a programming language from context
                prev_tokens = [doc[i].text.lower() for i in range(max(0, token.i-3), token.i)]
                next_tokens = [doc[i].text.lower() for i in range(token.i+1, min(len(doc), token.i+4))]
                context = ' '.join(prev_tokens + [token_text] + next_tokens)
                
                programming_indicators = [
                    'code', 'coding', 'program', 'programming', 'language', 'development',
                    'developer', 'script', 'scripting', 'software', 'application'
                ]
                
                if not any(indicator in context for indicator in programming_indicators):
                    continue
                
            matched_skills.add(token_text)
    
    # Additional pattern matching for skill extraction
    # 1. Programming language patterns
    prog_pattern = re.compile(r'\b(programming|coding|developing)\s+(in|with)\s+([A-Za-z\+\#]+)', re.IGNORECASE)
    for match in prog_pattern.finditer(text.lower()):
        skill = match.group(3).lower()
        if skill in single_word_skills and skill not in SKILL_STOPWORDS:
            matched_skills.add(skill)
    
    # 2. Technology/tool usage patterns
    tool_pattern = re.compile(r'\b(using|with|experience\s+in)\s+([A-Za-z\+\#]+)', re.IGNORECASE)
    for match in tool_pattern.finditer(text.lower()):
        skill = match.group(2).lower()
        if skill in single_word_skills and skill not in SKILL_STOPWORDS:
            matched_skills.add(skill)
    
    # 3. Additional patterns to extract tech terms based on common formats
    tech_patterns = [
        r'\b([A-Z][a-z]*[A-Z][a-zA-Z]*)\b',  # CamelCase (like JavaScript, TypeScript)
        r'\b([A-Z][a-z]+)\.(js|ts|py|java|rb)\b',  # Framework.js patterns (like React.js, Vue.js)
        r'\b([A-Z]{2,})\b'  # Acronyms (like HTML, CSS, AWS)
    ]
    
    for pattern in tech_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            potential_skill = match.group(0).lower()
            # Verify it's a known skill or a common tech term
            if (potential_skill in single_word_skills or 
                any(tech_term in potential_skill for tech_term in ['js', 'api', 'sdk', 'ui', 'ux'])):
                matched_skills.add(potential_skill)
    
    # Normalize and clean up the matched skills
    normalized_skills = []
    for skill in matched_skills:
        # Handle special cases for proper capitalization
        if skill.lower() in ['html', 'css', 'php', 'sql', 'aws', 'gcp', 'api', 'json', 'xml', 'ci/cd']:
            normalized_skills.append(skill.upper())
        elif skill.lower() in ['javascript', 'typescript', 'python', 'java', 'nodejs', 'react', 'angular']:
            normalized_skills.append(skill.capitalize())
        else:
            normalized_skills.append(skill)
    
    return sorted(normalized_skills)

def extract_location_from_text(text, nlp):
    """
    Extract location information from resume text.
    
    Args:
        text (str): The resume text
        nlp: spaCy loaded language model
        
    Returns:
        str: The identified location or empty string if none found
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Process the document
    doc = nlp(text)
    
    # First try to find location entities
    locations = []
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            locations.append(ent.text)
    
    # If entities found, return the most common one
    if locations:
        from collections import Counter
        location_counts = Counter(locations)
        return location_counts.most_common(1)[0][0]
    
    # If no entities found, look for common location patterns
    location_patterns = [
        r'(?i)Location\s*:\s*([A-Za-z\s,]+)',
        r'(?i)City\s*:\s*([A-Za-z\s,]+)',
        r'(?i)Address\s*:\s*([^,\n]+,[^,\n]+)',
        r'(?i)based in\s+([A-Za-z\s,]+)',
                r'(?i)based in\s+([A-Za-z\s,]+)',
        r'(?i)located in\s+([A-Za-z\s,]+)',
        r'(?i)(remote|work from home|wfh)',
    ]
    
    for pattern in location_patterns:
        matches = re.search(pattern, text)
        if matches:
            if len(matches.groups()) > 0:
                location = matches.group(1).strip()
                if location:
                    return location
            elif "remote" in matches.group(0).lower():
                return "Remote"
    
    return ""

def parse_resume_for_skills(resume_text):
    """
    Extract skills from a resume.
    
    Args:
        resume_text (str): Text from a resume
    
    Returns:
        list: Extracted skills from the resume
    """
    nlp, _ = load_spacy_model()
    skills = extract_skills_from_text(resume_text, nlp)
    return skills

# If the script is run directly, test the functionality
if __name__ == "__main__":
    test_text = """
    Job Description:
    We are looking for a skilled Python developer with experience in Django and Flask frameworks.
    The ideal candidate should have 3+ years of experience with REST API development,
    good knowledge of SQL databases (MySQL or PostgreSQL), and be familiar with AWS services.
    Experience with JavaScript, React, and Docker is a plus.
    """
    
    print("Testing skill extraction:")
    nlp, _ = load_spacy_model()
    skills = extract_skills_from_text(test_text, nlp)
    print(f"Extracted {len(skills)} skills: {skills}")

