from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('subs/', views.subs),
    path('command/', views.command),
    path('getdirs/', views.getDirs),
    path('changedir/', views.changeDir),
]
