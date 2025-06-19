from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .forms import VoiceResumeUploadForm
from .nlp_utils import extract_text, extract_skills
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

def upload_resume(request):
    if request.method == 'POST':
        form = VoiceResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = form.cleaned_data['resume']
            # Use binary stream for pdfminer
            resume_file.seek(0)
            text = extract_text(resume_file)  # pdfminer will now accept this
            skills = extract_skills(text)
            request.session['skills'] = skills
            return redirect('voice_assessment:select_skill')
    else:
        form = VoiceResumeUploadForm()
    return render(request, 'students/voice_interview/upload_resume.html', {'form': form})


def select_skill(request):
    skills = request.session.get('skills', [])
    if request.method == 'POST':
        selected_skills = request.POST.getlist('skills')
        request.session['skills'] = selected_skills
        request.session['question_index'] = 0
        request.session['score'] = 0
        request.session['feedback'] = []
        return redirect('voice_assessment:voice_to_voice')
    return render(request, 'students/voice_interview/skill_select.html', {'skills': skills})


def voice_to_voice(request):
    skills = request.session.get('skills', [])
    index = request.session.get('question_index', 0)

    if index >= len(skills):
        return redirect('voice_assessment:result')

    skill = skills[index]
    feedback = None
    question = request.session.get('current_question', '')

    if request.method == 'POST':
        if 'answer' in request.POST:
            answer = request.POST.get('answer', '').strip().lower()
            explanation_given = request.session.get('explanation_given', False)

            if ("explain" in answer or "can you explain" in answer) and not explanation_given:
                try:
                    explanation_response = openai.ChatCompletion.create(
                        model="llama3-8b-8192",
                        messages=[
                            {"role": "system", "content": f"You are a helpful tutor. Explain the concept behind this interview question on {skill} in simple terms."},
                            {"role": "user", "content": f"The question was: {question}"}
                        ]
                    )
                    explanation = explanation_response['choices'][0]['message']['content']
                    request.session['explanation'] = explanation
                    request.session['explanation_given'] = True
                    request.session['answered'] = False
                except Exception as e:
                    request.session['explanation'] = f"Error: {str(e)}"

                return render(request, 'students/voice_interview/voice_to_voice.html', {
                    'question': question,
                    'skill': skill,
                    'answered': False,
                    'feedback': None,
                    'explanation': request.session.get('explanation'),
                    'is_last_question': (index == len(skills) - 1)
                })

            try:
                eval_response = openai.ChatCompletion.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": f"You are an expert evaluating answers on {skill}. Provide a score (1–10) and short feedback."},
                        {"role": "user", "content": f"Answer: {answer}"}
                    ]
                )
                evaluation = eval_response['choices'][0]['message']['content']
            except Exception as e:
                evaluation = f"Error evaluating answer: {str(e)}"

            score = 0
            for word in evaluation.split():
                try:
                    word = word.replace('/10', '')
                    val = int(word)
                    if 0 <= val <= 10:
                        score = val
                        break
                except:
                    continue

            feedback_entry = {
                'skill': skill,
                'question': question,
                'student_answer': answer,
                'evaluation': evaluation,
                'score': score
            }

            feedback_list = request.session.get('feedback', [])
            feedback_list.append(feedback_entry)

            request.session['score'] = request.session.get('score', 0) + score
            request.session['feedback'] = feedback_list
            request.session['answered'] = True
            request.session['explanation_given'] = False
            feedback = feedback_entry

        elif 'next' in request.POST:
            request.session['question_index'] = index + 1
            request.session['answered'] = False
            request.session['current_question'] = ''
            request.session['explanation'] = ''
            return redirect('voice_assessment:voice_to_voice')

    if not request.session.get('answered', False) and not question:
        try:
            question_response = openai.ChatCompletion.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an interviewer."},
                    {"role": "user", "content": f"Ask a concise technical interview question on {skill}."}
                ]
            )
            question = question_response['choices'][0]['message']['content']
            request.session['current_question'] = question
        except Exception as e:
            question = f"Error generating question: {str(e)}"

    return render(request, 'students/voice_interview/voice_to_voice.html', {
        'question': question,
        'skill': skill,
        'answered': request.session.get('answered', False),
        'feedback': feedback,
        'explanation': request.session.get('explanation', None),
        'is_last_question': (index == len(skills) - 1)
    })


from django.shortcuts import render
from utils.db import db
from datetime import datetime

def result(request):
    feedback = request.session.get('feedback', [])
    total_score = request.session.get('score', 0)
    username = request.session.get('student_username')

    max_score = len(feedback) * 10
    percentage = int((total_score / max_score) * 100) if max_score else 0

    # Save to MongoDB if not already saved
    if username and feedback:
        simplified_responses = [
            {
                "question": f.get("question", "N/A"),
                "student_answer": f.get("student_answer", "N/A"),
                "score": f.get("score", 0)
            }
            for f in feedback
        ]

        # Optional: Check if already saved in session to prevent duplicates
        if not request.session.get("voice_saved"):
            db["voice_responses"].insert_one({
                "type": "voice",
                "username": username,
                "time": datetime.now(),
                "score": total_score,
                "total": max_score,
                "percentage": percentage,
                "responses": simplified_responses
            })
            request.session["voice_saved"] = True  # Prevent duplicate insert on reload

    return render(request, 'students/voice_interview/result.html', {
        'feedback': feedback,
        'score': total_score,
        'max_score': max_score,
        'percentage': percentage
    })
