from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('subs/', views.subs),
    path('media/', views.media),
    path('command/', views.command),
    path('getdirs/', views.getDirs),
    path('changedir/', views.changeDir),
    path('appendtoplaylist/', views.appendToPlaylist),
    path('playnow/', views.playNow),
]
