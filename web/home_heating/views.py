from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from home_heating.view import ebusd_reader

@login_required
def debug_ebus(request):
    return HttpResponse(ebusd_reader.read_all_ebus_values(), content_type="application/json")

