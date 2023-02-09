from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from home_energy.view import get_latest
from home_energy.view import get_detailed_usage
from home_energy.view import p1_reader_debug

@login_required
def usage(request):
    return render(request, 'home_energy/usage.html')

@login_required
def latest(request):
    return HttpResponse(get_latest.get_latest(), content_type="application/json")

@login_required
def details(request):
    date = request.GET.get('date', '')
    mode = request.GET.get('mode', 1)
    return HttpResponse(get_detailed_usage.get_detailed_usage(date, mode), content_type="application/json")

@login_required
def prices(request):
    return render(request, 'home_energy/prices.html')

@login_required
def debug_p1_reader(request):
    context = {'debug_entries': p1_reader_debug.get_debug_entries()}
    return render(request, 'home_energy/debug/p1-reader.html', context)
