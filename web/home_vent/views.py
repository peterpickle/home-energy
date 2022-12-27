from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render

from home_vent.view import get_vent_data
import json
import paho.mqtt.client as mqtt

@login_required
def main(request):
    return render(request, 'home_vent/main.html')

@login_required
def get(request, field):
    return HttpResponse(get_vent_data.get(field), content_type="application/json")

@login_required
def getAll(request):
    return HttpResponse(get_vent_data.get_all(), content_type="application/json")

@login_required
def action(request, action):
    mqtt_client = mqtt.Client()
    mqtt_client.connect('127.0.0.1', 1883, 60)
    message_info = mqtt_client.publish('comfoair/action', action)
    message_info.wait_for_publish()
    if message_info.rc == mqtt.MQTT_ERR_SUCCESS:
        result = "ok"
    else:
        result = "error"
    mqtt_client.disconnect()
    return HttpResponse(json.dumps(result), content_type="application/json")
