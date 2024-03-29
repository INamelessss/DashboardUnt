from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
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

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect("login")
    else:
        return redirect("login")
