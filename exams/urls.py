from django.urls import path

from .views import (
    exam_view,
    success_view,
    logout_view,
    exam_violation,
    result_view,
    exam_analytics_view,
    instructor_dashboard_view,
    post_login_redirect,
    student_dashboard_view,
)

from django.contrib.auth import views as auth_views


urlpatterns = [

    path(
        '',
        auth_views.LoginView.as_view(
            template_name='login.html',
            redirect_authenticated_user=True
        ),
        name='home'
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    path(
        'redirect/',
        post_login_redirect,
        name='post_login_redirect'
    ),

    path(
        'student/dashboard/',
        student_dashboard_view,
        name='student_dashboard'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    path(
        'instructor/dashboard/',
        instructor_dashboard_view,
        name='instructor_dashboard'
    ),

    path(
        'exam/<int:exam_id>/',
        exam_view,
        name='exam_view'
    ),

    path(
        'exam/<int:exam_id>/violation/',
        exam_violation,
        name='exam_violation'
    ),

    path(
        'result/<int:exam_id>/',
        result_view,
        name='result_view'
    ),

    path(
        'exam/<int:exam_id>/analytics/',
        exam_analytics_view,
        name='exam_analytics'
    ),

    path(
        'success/',
        success_view,
        name='success_view'
    ),
]