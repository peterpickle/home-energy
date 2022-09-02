from django.urls import path

from . import views

app_name = 'home-heating'
urlpatterns = [
    # ex: /home-heating/
    # ex: /home-heating/index.html
    path('', views.index, name='index'),
    path('index.html', views.index, name='index'),

    # ex: /home-heating/get/<circuit>/<field>
    path('get/<str:circuit>/<str:field>', views.get, name='get'),

    # ex: /home-heating/set/<circuit>/<field>/value
    path('set/<str:circuit>/<str:field>/<str:value>', views.set, name='set'),

    # ex: /home-heating/debug/ebus
    # ex: /home-heating/debug/ebus/
    path('debug/ebus', views.debug_ebus, name='debug_ebus'),
    path('debug/ebus/', views.debug_ebus, name='debug_ebus'),
]
