import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from utils.db import db  # your mongo helper
from instructors.token_logger import log_token_history

import pandas as pd
import plotly.express as px
import plotly.offline as opy

# Custom decorator to check if the user is an instructor
def instructor_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect("instructor_panel:login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login_instructor(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()

        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            auth.login(request, user)
            return redirect("instructor_panel:dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("instructor_panel:login")

    return render(request, "instructors/login.html")

def logout_instructor(request):
    auth.logout(request)
    return redirect("instructor_panel:login")

@login_required
@instructor_required
def dashboard(request):
    instructor_username = request.user.username

    access_col = db["access_students"]
    results_col = db["results"]
    logs_col = db["token_logs"]

    # Search students
    search_query = request.GET.get("search", "").lower()
    students = list(access_col.find({}))
    filtered_students = [
        s for s in students if
        search_query in s.get("username", "").lower() or
        search_query in s.get("name", "").lower()
    ]

    # Prepare token management data
    token_data = []
    for s in filtered_students:
        token_data.append({
            "username": s["username"],
            "name": s.get("name", "Unknown"),
            "tokens": s.get("tokens", 0),
            "exam_attempts": s.get("exam_attempts", 0),
            "ai_tokens": s.get("ai_tokens", {
                "Text_to_Text": 0,
                "Voice_to_Voice": 0,
                "Face_to_Face": 0,
            }),
        })

    # Prepare token logs (latest 100)
    logs = list(logs_col.find({"instructor": instructor_username}).sort("timestamp", -1).limit(100))

    # Analytics - tokens per student chart
    token_chart_df = pd.DataFrame([{
        "username": s["username"],
        "tokens_left": s.get("tokens", 0),
        "Text-to-Text": s.get("ai_tokens", {}).get("Text_to_Text", 0),
        "Voice-to-Voice": s.get("ai_tokens", {}).get("Voice_to_Voice", 0),
        "Face-to-Face": s.get("ai_tokens", {}).get("Face_to_Face", 0),
    } for s in students])

    fig1 = px.bar(token_chart_df, x="username", y=["tokens_left", "Text-to-Text", "Voice-to-Voice", "Face-to-Face"],
                  barmode="group", title="Tokens Per Student")
    token_chart_div = opy.plot(fig1, auto_open=False, output_type='div')

    # Assessment results for analytics
    result_docs = list(results_col.find({}))
    if result_docs:
        score_data = []
        for r in result_docs:
            score_data.append({
                "username": r.get("username", "unknown"),
                "score": r.get("score", 0),
                "timestamp": r.get("timestamp", now()),
                "skill": r.get("skill", "Unknown Skill"),
            })

        score_df = pd.DataFrame(score_data)
        score_df["timestamp"] = pd.to_datetime(score_df["timestamp"])

        fig2 = px.line(score_df, x="timestamp", y="score", color="username",
                       title="Assessment Scores Over Time")
        score_chart_div = opy.plot(fig2, auto_open=False, output_type='div')

        # Student ranking summary
        summary_df = score_df.groupby("username").agg({
            "score": ["count", "mean", "max"]
        }).reset_index()
        summary_df.columns = ["Username", "Attempts", "Average Score", "Max Score"]
        summary_df = summary_df.sort_values(by="Average Score", ascending=False)
        summary_html = summary_df.to_html(classes="table table-striped", index=False)

    else:
        score_chart_div = None
        summary_html = None

    context = {
        "instructor_username": instructor_username,
        "students": token_data,
        "logs": logs,
        "token_chart_div": token_chart_div,
        "score_chart_div": score_chart_div,
        "summary_html": summary_html,
        "search_query": search_query,
    }
    return render(request, "instructors/dashboard.html", context)

@csrf_exempt
@login_required
@instructor_required
def update_token(request):
    if request.method != "POST":
        return HttpResponseForbidden()

    data = json.loads(request.body)
    username = data.get("username")
    action = data.get("action")
    module = data.get("module")  # Optional
    value = int(data.get("value", 0))
    instructor_username = request.user.username

    access_col = db["access_students"]
    log_module = module or "general"
    update_query = {}

    if action == "reset_all":
        update_query = {
            "$set": {
                "tokens": 15,
                "ai_tokens": {
                    "Text_to_Text": 15,
                    "Voice_to_Voice": 15,
                    "Face_to_Face": 15,
                },
            },
            "$inc": {"exam_attempts": 1},
        }
        log_token_history(username, instructor_username, "Reset to 15", 15)
    elif module:
        update_query = {"$inc": {f"ai_tokens.{module}": value}}
        log_token_history(
            username,
            instructor_username,
            f"Module Token {'Increment' if value > 0 else 'Decrement'}",
            value,
            module,
        )
    else:
        update_query = {"$inc": {"tokens": value}}
        log_token_history(
            username,
            instructor_username,
            f"Token {'Increment' if value > 0 else 'Decrement'}",
            value,
        )

    result = access_col.update_one({"username": username}, update_query)
    if result.modified_count == 1:
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Update failed"})