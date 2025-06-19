from django.shortcuts import render, redirect
from django.contrib import messages
from bson.objectid import ObjectId
from utils.db import db
from django.http import HttpResponse
import pandas as pd

reg_col = db["student_registrations"]
access_col = db["access_students"]
not_access_col = db["not_access_students"]
course_col = db["courses"]
logs_col = db["instructor_logs"]

# Admin login credentials (use env variables in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session['admin_logged_in'] = True
            request.session['admin_user'] = username
            return redirect('admin_panel:dashboard')
        else:
            messages.error(request, "Invalid admin credentials")

    return render(request, 'admin_panel/login.html')

def admin_logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('admin_panel:login')

def dashboard(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_panel:login')

    pending_students = list(reg_col.find())
    approved_students = list(access_col.find())
    rejected_students = list(not_access_col.find())

    pending_courses = list(course_col.find({"status": "pending"}))
    approved_courses = list(course_col.find({"status": "approved"}))
    rejected_courses = list(course_col.find({"status": "rejected"}))

    logs = list(logs_col.find().sort("timestamp", -1))[:50]

    # Convert ObjectId _id to string for template usage
    for student in pending_students + approved_students + rejected_students:
        student['id_str'] = str(student['_id'])
    for course in pending_courses + approved_courses + rejected_courses:
        course['id_str'] = str(course['_id'])
    for log in logs:
        if 'timestamp' in log:
            log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    context = {
        'pending_students': pending_students,
        'approved_students': approved_students,
        'rejected_students': rejected_students,
        'pending_courses': pending_courses,
        'approved_courses': approved_courses,
        'rejected_courses': rejected_courses,
        'logs': logs
    }
    return render(request, 'admin_panel/dashboard.html', context)

def approve_student(request, student_id):
    user = reg_col.find_one({"_id": ObjectId(student_id)})
    if user:
        access_col.insert_one(user)
        reg_col.delete_one({"_id": ObjectId(student_id)})
    return redirect('admin_panel:dashboard')

def reject_student(request, student_id):
    user = reg_col.find_one({"_id": ObjectId(student_id)})
    if user:
        not_access_col.insert_one(user)
        reg_col.delete_one({"_id": ObjectId(student_id)})
    return redirect('admin_panel:dashboard')

def update_student(request, student_id):
    if request.method == 'POST':
        reg_col.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {
                "name": request.POST.get("name"),
                "email": request.POST.get("email"),
                "username": request.POST.get("username")
            }}
        )
    return redirect('admin_panel:dashboard')

def approve_course(request, course_id):
    course_col.update_one({"_id": ObjectId(course_id)}, {"$set": {"status": "approved"}})
    return redirect('admin_panel:dashboard')

def reject_course(request, course_id):
    course_col.update_one({"_id": ObjectId(course_id)}, {"$set": {"status": "rejected"}})
    return redirect('admin_panel:dashboard')

def download_approved_students(request):
    approved = list(access_col.find())
    df = pd.DataFrame(approved)
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    csv_data = df.to_csv(index=False)
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="approved_students.csv"'
    return response
