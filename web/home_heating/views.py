from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from home_heating.view import ebusd_reader

@login_required
def index(request):
    return render(request, 'home_heating/index.html')

@login_required
def get(request, circuit, field):
    return HttpResponse(ebusd_reader.read(circuit, field), content_type="application/json")

@login_required
def set(request, circuit, field, value):
    return HttpResponse(ebusd_reader.write(circuit, field, value), content_type="application/json")

@login_required
def debug_ebus(request):
    return HttpResponse(ebusd_reader.read_all_ebus_values(), content_type="application/json")
