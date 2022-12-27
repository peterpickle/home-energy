from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from home_vent.view import get_vent_data

@login_required
def main(request):
    return render(request, 'home_vent/main.html')

@login_required
def get(field):
    return HttpResponse(get_vent_data.get(field), content_type="application/json")

@login_required
def getAll(request):
    return HttpResponse(get_vent_data.get_all(), content_type="application/json")
