from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from home_energy.view import get_latest
from home_energy.view import get_detailed_usage
from home_energy.view import p1_reader_debug

#@login_required(login_url='/accounts/login/')

def usage(request):
    return render(request, 'home_energy/usage.html')

def latest(request):
    return HttpResponse(get_latest.get_latest(), content_type="application/json")

def details(request):
    date = request.GET.get('date', '')
    mode = request.GET.get('mode', 1)
    return HttpResponse(get_detailed_usage.get_detailed_usage(date, mode), content_type="application/json")

def debug_p1_reader(request):
    context = {'debug_entries': p1_reader_debug.get_debug_entries()}
    return render(request, 'home_energy/debug/p1-reader.html', context)
