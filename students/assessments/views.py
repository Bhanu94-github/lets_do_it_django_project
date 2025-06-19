from django.shortcuts import render, redirect
from .forms import ResumeUploadForm
from .nlp_utils import extract_text, extract_skills
from .mongo_helper import get_all_questions, save_result
from datetime import datetime
import random

def clean_question(q):
    q = dict(q)
    q.pop('_id', None)
    return q

# Resume upload and skill extraction
def upload_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['resume']
            text = extract_text(file)
            skills = extract_skills(text)
            request.session['skills'] = skills
            return redirect('student_assessments:select_difficulty')
    else:
        form = ResumeUploadForm()
    return render(request, 'students/upload_resume.html', {'form': form})

# Skill + difficulty selection screen
def select_difficulty(request):
    skills = request.session.get('skills', [])
    if request.method == 'POST':
        request.session['skill'] = request.POST['skill']
        request.session['difficulty'] = request.POST['difficulty']
        return redirect('student_assessments:prepare_exam')
    return render(request, 'students/select_difficulty.html', {'skills': skills})

# Pull questions and prepare the exam session
def prepare_exam(request):
    skill = request.session['skill']
    difficulty = request.session['difficulty']

    # Use helper function to get questions
    questions = get_all_questions(skill, difficulty)

    # Separate by type
    mcqs = [q for q in questions if q.get('type') == 'mcqs']
    blanks = [q for q in questions if q.get('type') == 'blanks']
    coding = [q for q in questions if q.get('type') == 'coding']

    # Set minimum counts
    min_mcqs = 8
    min_blanks = 5
    min_coding = 2

    if len(mcqs) < min_mcqs or len(blanks) < min_blanks or len(coding) < min_coding:
        return render(request, 'students/select_difficulty.html', {
            'skills': request.session.get('skills', []),
            'error': f'Not enough questions for "{skill}" at "{difficulty}". '
                     f'Available: {len(mcqs)} MCQs, {len(blanks)} Blanks, {len(coding)} Coding.'
        })

    sampled_mcqs = random.sample(mcqs, min_mcqs)
    sampled_blanks = random.sample(blanks, min_blanks)
    sampled_coding = random.sample(coding, min_coding)

    sampled = sampled_mcqs + sampled_blanks + sampled_coding
    random.shuffle(sampled)

    request.session['questions'] = [clean_question(q) for q in sampled]
    request.session['index'] = 0
    request.session['responses'] = []

    return redirect('student_assessments:exam')

# Exam navigation + answer selection
def exam(request):
    questions = request.session.get('questions', [])
    index = request.session.get('index', 0)
    total = len(questions)

    if request.method == 'POST':
        selected = request.POST.get('answer')
        action = request.POST.get('action')
        responses = request.session.get('responses', [])

        if selected:
            if len(responses) > index:
                responses[index]['selected'] = selected
            else:
                responses.append({
                    'question': questions[index]['question'],
                    'selected': selected,
                    'correct': questions[index].get('answer'),
                    'type': questions[index].get('type'),
                })
            request.session['responses'] = responses
        else:
            return render(request, 'students/exam.html', {
                'question': questions[index],
                'index': index + 1,
                'total': total,
                'selected': '',
                'error': 'Please select an option.'
            })

        if action == 'next':
            index = min(index + 1, total - 1)
        elif action == 'prev':
            index = max(index - 1, 0)
        elif action == 'submit':
            return redirect('student_assessments:result')

        request.session['index'] = index
        return redirect('student_assessments:exam')

    selected = ''
    responses = request.session.get('responses', [])
    if index < len(responses):
        selected = responses[index].get('selected', '')

    return render(request, 'students/exam.html', {
        'question': questions[index],
        'index': index + 1,
        'total': total,
        'selected': selected
    })

# Save result and show summary
def result(request):
    responses = request.session.get('responses', [])
    correct_count = 0

    for r in responses:
        selected = r.get('selected')
        correct = r.get('correct')
        if selected and correct and selected.strip().lower() == correct.strip().lower():
            correct_count += 1

    total = len(responses)
    percentage = int((correct_count / total) * 100) if total else 0

    # Save result using helper
    result_data = {
        "username": request.session.get("student_username"),
        "skill": request.session.get("skill"),
        "difficulty": request.session.get("difficulty"),
        "score": percentage,
        "correct": correct_count,
        "total": total,
        "timestamp": datetime.now(),
        "responses": responses,
        "type": "exam"
    }
    save_result(result_data)

    return render(request, 'students/result.html', {
        'responses': responses,
        'correct_count': correct_count,
        'total': total,
        'percentage': percentage
    })
