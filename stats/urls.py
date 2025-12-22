from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from stats.views import rankings_view, player_stats_view

urlpatterns = [
    path('', rankings_view.weekly_rankings_view, name='home'),
    path('weekly/', rankings_view.weekly_rankings_view, name='weekly_rankings'),
    path('season/', rankings_view.season_rankings_view, name='season_rankings'),
    path('playerstats/', player_stats_view.player_stats_view, name= 'player_stats'),


]