from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),


    path('my-posts/', views.MyPostsView.as_view(), name='my_posts'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('search/', views.SearchView.as_view(), name='search_results'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', views.custom_logout_view, name='logout'), 
    path('post/new/', views.PostCreateView.as_view(), name='create_post'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='update_post'),
    path('check-username/', views.CheckUsernameView.as_view(), name='check_username'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='delete_post'),
    path('user/<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),
    path('user/<str:username>/follow/', views.FollowView.as_view(), name='follow_user'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('post/<int:pk>/vote/', views.PostVoteView.as_view(), name='post_vote'),
]