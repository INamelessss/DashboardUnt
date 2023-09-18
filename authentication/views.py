from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import JsonResponse

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})
    return render(request, "authentication/login.html")

