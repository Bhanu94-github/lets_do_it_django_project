from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect
from utils.mongo import get_collection
import json
from functools import wraps
from uuid import uuid4
from datetime import datetime
from utils.db import db  # ✅ Use shared db object
from instructors.token_logger import log_token_history

# -------------------- Registration --------------------
@csrf_exempt
def register_student(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            registrations = get_collection("student_registrations", db="instructor")

            if registrations.find_one({"$or": [{"email": email}, {"username": username}]}):
                return JsonResponse({"status": "error", "message": "Email or Username already registered"})

            registrations.insert_one({
                "name": name,
                "username": username,
                "email": email,
                "password": password,
                "approved": False
            })

            return JsonResponse({
                "status": "success",
                "message": "Registration submitted. Awaiting admin approval."
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"})


# -------------------- Login --------------------
@csrf_exempt
def login_student(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            students = get_collection("access_students", db="instructor")
            user = students.find_one({"email": email, "password": password})
            
            if user:
                request.session['student_email'] = email
                request.session['student_username'] = user.get("username", user.get("name", ""))
                return JsonResponse({
                    "status": "success",
                    "message": "Login successful",
                    "user": user.get("username", user.get("name", ""))
                })

            return JsonResponse({"status": "error", "message": "Invalid credentials"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"})


# -------------------- Custom Login Required Decorator --------------------
def student_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'student_email' not in request.session:
            return redirect('students:student_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# -------------------- Dashboard --------------------
@student_login_required
def dashboard(request):
    email = request.session.get('student_email')
    students = get_collection("access_students", db="instructor")
    student = students.find_one({"email": email})

    if not student:
        return redirect('students:student_login')

    return render(request, 'students/dashboard.html', {
        "user": {
            "username": student.get("username", ""),
            "name": student.get("name", ""),
            "email": student.get("email", ""),
            "ai_tokens": student.get("ai_tokens", {
                "Text_to_Text": 0,
                "Voice_to_Voice": 0,
                "Face_to_Face": 0
            })
        }
    })


# -------------------- Profile Update --------------------
@csrf_exempt
@student_login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            email = request.session.get('student_email')
            students = get_collection("access_students", db="instructor")

            name = request.POST.get("name")
            new_email = request.POST.get("email")
            password = request.POST.get("password")

            updates = {}
            if name:
                updates["name"] = name
            if new_email:
                updates["email"] = new_email
            if password:
                updates["password"] = password

            if updates:
                students.update_one({"email": email}, {"$set": updates})
                if new_email:
                    request.session['student_email'] = new_email

            return redirect('students:student_dashboard')
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"})


# -------------------- Token Exam Launch Handler --------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from uuid import uuid4  # for session tracking
from instructors.token_logger import log_token_history  # or your actual logger
from utils.db import db  # assuming you're using a helper for db connection

@student_login_required
def start_ai_exam(request, module):
    username = request.session.get("student_username")
    user = db["access_students"].find_one({"username": username})

    if not user:
        messages.error(request, "User not found.")
        return redirect("students:dashboard")

    # Convert module name to token key format (e.g., "Text-to-Text" => "text_to_text")
    token_key = module.replace("-", "_").lower()

    # Get token key in DB (case-insensitive match)
    ai_tokens = user.get("ai_tokens", {})
    matching_key = next((k for k in ai_tokens if k.lower() == token_key), None)

    if not matching_key:
        messages.error(request, f"No tokens found for {module} module.")
        return redirect("students:dashboard")

    tokens_left = ai_tokens.get(matching_key, 0)

    # Avoid multiple deductions if already active
    if request.session.get("exam_active"):
        messages.info(request, "You already have an active exam.")
        return redirect("students:dashboard")

    if tokens_left > 0:
        result = db["access_students"].update_one(
            {"username": username, f"ai_tokens.{matching_key}": {"$gt": 0}},
            {"$inc": {f"ai_tokens.{matching_key}": -1}}
        )

        if result.modified_count == 1:
            # Log token use
            log_token_history(
                student_username=username,
                instructor_username="self-service",
                action="Token Used",
                tokens_changed=-1,
                module=matching_key
            )

            # Track exam session
            request.session["exam_active"] = True
            request.session["selected_module"] = matching_key
            request.session["session_id"] = str(uuid4())

            # Redirect based on module
            if module == "Text-to-Text":
                return redirect("student_assessments:upload_resume")
            elif module == "Voice-to-Voice":
                return redirect("voice_assessment:upload_resume")
            elif module == "Face-to-Face":
                return redirect("face_assessment:upload_resume")  # if exists
            else:
                messages.error(request, "Unknown module selected.")
                return redirect("students:dashboard")
        else:
            messages.error(request, "Failed to deduct token.")
            return redirect("students:dashboard")
    else:
        messages.error(request, f"No tokens left for {module} module.")
        return redirect("students:dashboard")



# -------------------- Login Success Redirect --------------------
def login_success_redirect(request):
    response = redirect('students:dashboard')
    response.set_cookie('resetTimer', 'true')
    return response
from django.http import JsonResponse
from django.shortcuts import redirect

@csrf_exempt
def save_time(request):
    if request.method == "POST":
        data = json.loads(request.body)
        time_spent = data.get("time_spent")
        is_logout = data.get("logout", False)

        # Save time logic here...

        if is_logout:
            request.session.flush()
            return JsonResponse({"status": "logged out"})

        return JsonResponse({"status": "saved"})

from django.shortcuts import render

# students/views.py
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')  # ✅ No 'students/' prefix

from django.http import JsonResponse
from utils.db import db  # adjust if your DB connection is different

def get_tokens(request):
    username = request.session.get("student_username")

    if not username:
        return JsonResponse({"error": "Not logged in"}, status=401)

    student = db.access_students.find_one({"username": username})

    if not student:
        return JsonResponse({"error": "Student not found"}, status=404)

    ai_tokens = student.get("ai_tokens", {})
    return JsonResponse({
        "tokens": {
            "text_to_text": ai_tokens.get("Text_to_Text", 0),
            "voice_to_voice": ai_tokens.get("Voice_to_Voice", 0),
            "face_to_face": ai_tokens.get("Face_to_Face", 0)
        }
    })

