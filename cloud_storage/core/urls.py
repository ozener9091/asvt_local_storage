from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('files/', views.file_list, name='file_list'),
    path('files/folder/<uuid:folder_id>/', views.folder_view, name='folder_view'),
    path('upload/', views.upload_file, name='upload'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('delete/<uuid:file_id>/', views.delete_file, name='delete_file'),
    path('download/<uuid:file_id>/', views.download_file, name='download_file'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]