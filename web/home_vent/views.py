from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

@login_required
def main(request):
    return render(request, 'home_vent/main.html')
