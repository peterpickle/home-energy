import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from home_energy.forms import *

from home_energy.view import energy_common as ec
from home_energy.view import usage as u
from home_energy.view import p1_reader_debug
from home_energy.view import prices as pr
from home_energy.view import cost

import json

@login_required
def usage(request):
    return render(request, 'home_energy/usage.html')

@login_required
def latest_usage(request):
    return HttpResponse(json.dumps(u.get_latest_usage()), content_type="application/json")

@login_required
def detailed_usage(request):
    date = request.GET.get('date', '')
    mode = request.GET.get('mode', 1)
    detailed_usage = u.get_detailed_usage(date, mode)
    return HttpResponse(json.dumps(detailed_usage), content_type="application/json")

@login_required
def total_usage(request):
    form = GetTotalsForm(request.GET)
    if form.is_valid():
        starttime = ec.get_epoch_time_s(form.cleaned_data['startdate'])
        endtime = ec.get_epoch_time_s(form.cleaned_data['enddate'] + datetime.timedelta(days=1))
        mode = form.cleaned_data['mode']
        total_usage = u.get_total_usage(starttime, endtime, mode)
    else:
        return HttpResponse(json.dumps({"errors" : form.errors}), content_type="application/json")
    return HttpResponse(json.dumps(total_usage), content_type="application/json")

@login_required
def total_cost(request):
    form = GetTotalsForm(request.GET)
    if form.is_valid():
        starttime = ec.get_epoch_time_s(form.cleaned_data['startdate'])
        endtime = ec.get_epoch_time_s(form.cleaned_data['enddate'] + datetime.timedelta(days=1))
        mode = form.cleaned_data['mode']
        total_costs = cost.get_total_costs(starttime, endtime, mode)
    else:
        return HttpResponse(json.dumps({"errors" : form.errors}), content_type="application/json")
    return HttpResponse(json.dumps(total_costs), content_type="application/json")


def get_modify_price_forms():
    prices = pr.get_all_prices_reversed()
    modify_price_forms = []
    for price in prices:
        epoch = ec.get_datetime_from_epoch_in_s(int(price['starttime']))
        price['starttime'] = ec.format_epoch(epoch, "%Y-%m-%d")
        modify_price_forms.append(ModifyPriceForm(price))
    return modify_price_forms

@login_required
def prices(request):
    context = {
        'add_price_form': AddPriceForm(),
        'modify_price_forms' : get_modify_price_forms(),
    }
    return render(request, 'home_energy/prices.html', context)

@login_required
def get_all_prices(request):
    return HttpResponse(json.dumps(pr.get_all_prices_reversed()), content_type="application/json")

@login_required
def add_price(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('home-energy:prices'))

    form = AddPriceForm(request.POST)

    if form.is_valid():
        starttime = form.cleaned_data['starttime']
        rates = {k: v for k, v in form.cleaned_data.items() if k != 'starttime' and v is not None}
        rv = pr.add_price(ec.get_epoch_time_s(starttime), rates)
        if rv != -1:
            return HttpResponseRedirect(reverse('home-energy:prices'))
        else:
            form.add_error(None, 'Failed to add price.')

    context = {
        'add_price_form': form,
        'modify_price_forms' : get_modify_price_forms(),
    }

    return render(request, 'home_energy/prices.html', context)

@login_required
def modify_price(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('home-energy:prices'))

    form = ModifyPriceForm(request.POST)

    if form.is_valid():
        starttime = form.cleaned_data['starttime']
        rates = {k: v for k, v in form.cleaned_data.items() if k != 'starttime' and k != 'id' and v is not None}
        rv = pr.modify_price(form.cleaned_data['id'], ec.get_epoch_time_s(starttime), rates)
        if rv != -1:
            return HttpResponseRedirect(reverse('home-energy:prices'))
        else:
            form.add_error(None, 'Failed to modify price.')

    #replace the empty form in the list with the one with errors in it
    modify_price_forms = get_modify_price_forms()
    for i in range(len(modify_price_forms)):
        f = modify_price_forms[i]
        if f.is_valid() and f.cleaned_data['id'] == form.cleaned_data['id']:
            modify_price_forms[i] = form
            break

    context = {
        'add_price_form': AddPriceForm(),
        'modify_price_forms' : modify_price_forms,
    }

    return render(request, 'home_energy/prices.html', context)

@login_required
def remove_price(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('home-energy:prices'))

    form = RemovePriceForm(request.POST)

    if form.is_valid():
        pr.remove_price(form.cleaned_data['id'])

    return HttpResponseRedirect(reverse('home-energy:prices'))

@login_required
def debug_p1_reader(request):
    context = {'debug_entries': p1_reader_debug.get_debug_entries()}
    return render(request, 'home_energy/debug/p1-reader.html', context)
