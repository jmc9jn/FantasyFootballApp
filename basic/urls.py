from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from basic.views import views

urlpatterns = [
    path('', views.weekly_rankings_view, name='home'),
    path('weekly/', views.weekly_rankings_view, name='weekly_rankings'),
    path('season/', views.season_rankings_view, name='season_rankings'),
    path('playerstats/', views.player_stats_view, name= 'player_stats'),
    path("defense-weekly/", views.defense_weekly_stats),


]