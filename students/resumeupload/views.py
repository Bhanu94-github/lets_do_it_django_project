import os
import fitz  # PyMuPDF
from docx import Document
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse, HttpResponseNotFound
from django.core.files.storage import default_storage
from django.conf import settings
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def extract_text_from_resume(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    elif ext in [".docx", ".doc"]:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        text = "Unsupported file type"
    return text


def analyze_resume_with_groq(resume_text):
    prompt = f"""
You are an AI resume analyst. Given this resume text, evaluate its:
- ATS compatibility
- Skill relevance
- Formatting
- Suggestions for improvement

Resume:
\"\"\"{resume_text}\"\"\"

Give a score out of 100 and detailed feedback.
"""
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert in resume evaluation."},
                {"role": "user", "content": prompt}
            ]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error analyzing resume: {str(e)}"


@csrf_exempt
def upload_resume(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("resume")
        if not uploaded_file:
            return render(request, "students/resumeupload/upload.html", {"error": "No file uploaded."})

        file_path = default_storage.save(uploaded_file.name, uploaded_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        try:
            resume_text = extract_text_from_resume(full_path)
            feedback = analyze_resume_with_groq(resume_text)
        except Exception as e:
            return render(request, "students/resumeupload/upload.html", {"error": f"❌ Error: {e}"})

        # Generate PDF feedback
        feedback_pdf_name = f"feedback_{os.path.splitext(uploaded_file.name)[0]}.pdf"
        feedback_pdf_path = os.path.join(settings.MEDIA_ROOT, feedback_pdf_name)

        doc = fitz.open()
        page = doc.new_page()
        rect = fitz.Rect(40, 40, 550, 800)
        text = feedback
        page.insert_textbox(rect, text, fontsize=11, color=(0, 0, 0))
        doc.save(feedback_pdf_path)

        return render(request, "students/resumeupload/upload.html", {
            "message": "✅ Resume analyzed successfully!",
            "feedback": feedback.replace("**", ""),
            "feedback_pdf_name": feedback_pdf_name,
        })

    return render(request, "students/resumeupload/upload.html")


def download_feedback(request):
    file_name = request.GET.get("file")
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_name)
    return HttpResponseNotFound("File not found.")
