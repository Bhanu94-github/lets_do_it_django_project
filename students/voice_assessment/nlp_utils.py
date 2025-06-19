import spacy
from spacy.matcher import PhraseMatcher
import PyPDF2
import docx

nlp = spacy.load("en_core_web_sm")

ALL_SKILLS = [
    "python", "sql", "java", "javascript", "html", "css", "c++", "mongodb",
    "machine learning", "data analysis", "nlp", "pandas", "numpy", "django"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
skill_patterns = [nlp.make_doc(skill.lower()) for skill in ALL_SKILLS]
matcher.add("SKILLS", None, *skill_patterns)

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.content_type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text()
        elif uploaded_file.content_type == "text/plain":
            text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print("Error reading resume:", e)
    print("Extracted Text (Preview):", text[:300])
    return text

def extract_skills(text):
    doc = nlp(text.lower())
    matches = matcher(doc)
    found_skills = list({doc[start:end].text for match_id, start, end in matches})
    print("Matched skills:", found_skills)
    return found_skills
