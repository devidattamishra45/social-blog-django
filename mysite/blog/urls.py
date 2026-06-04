from django.urls import path
from django.contrib.auth import views as auth_views
from .feeds import LatestPostsFeed
from . import views

app_name = "blog"

urlpatterns = [
    # Post queries
    path("", views.post_list, name="post_list"),
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),
    path("<int:id>/", views.post_detail, name="post_detail"),
    path("<int:post_id>/share/", views.post_share, name="post_share"),
    path("feed/", LatestPostsFeed(), name="post_feed"),

    # User Authentication
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="blog/registration/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="blog:post_list"),
        name="logout",
    ),

    # Profiles & Dashboards
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/<str:username>/", views.profile_view, name="profile_view"),
    path("dashboard/", views.dashboard_view, name="dashboard_view"),

    # Post CRUD
    path("post/new/", views.post_create, name="post_create"),
    path("post/<int:id>/edit/", views.post_edit, name="post_edit"),
    path("post/<int:id>/delete/", views.post_delete, name="post_delete"),
]