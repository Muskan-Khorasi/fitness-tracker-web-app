from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('workouts/', views.workout_list, name='workout_list'),
    path('add/', views.add_workout, name='add_workout'),
    path('edit/<int:pk>/', views.edit_workout, name='edit_workout'),
    path('delete/<int:pk>/', views.delete_workout, name='delete_workout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('progress/', views.progress, name='progress'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]