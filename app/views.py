from django.http import JsonResponse
from django.shortcuts import render
import json
import os


def health(request):
    return JsonResponse({"status": "healthy"})


def dashboard(request):
    status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "status.json")

    with open(status_file, "r") as file:
        status_data = json.load(file)

    return render(request, "dashboard.html", {"status": status_data})