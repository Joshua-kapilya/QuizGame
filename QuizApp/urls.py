from django.urls import path
from .views import select_quiz_mode, get_questions  # Only import existing views
from. import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),  # Home - Select Subject
    path('signup/', views.signup, name='signup'),
    path('login_view/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('quiz-mode/<int:subject_id>/', select_quiz_mode, name='select_quiz_mode'),  # Select past paper or random
    path('questions/<int:subject_id>/', get_questions, name='get_questions'),  # Display questions
    path("check-answer/", views.check_answer, name="check_answer"),
    path('get_explanation/<int:question_id>/', views.get_explanation, name='get_explanation'),
    path("tournaments/", views.tournament_list, name="tournament_list"),
    path('tournament_detail/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path("subject/<int:subject_id>/questions/", views.subject_questions, name="subject_questions"),
    path("tournament/<int:subject_id>/submit/", views.submit_tournament_quiz, name="submit_tournament_quiz"),
    path("profile/", views.profile_view, name="profile_view"),
   # path("enrollment/", views.enrollment, name="enrollment"),
   path("profile/update/", views.update_profile, name="update_profile"),
   path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset.html'), 
         name='password_reset'),

    path('password_reset_done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),

    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),


]
