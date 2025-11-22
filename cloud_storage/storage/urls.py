from django.urls import path
from .import views


app_name ='storage'

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.file_list, name='file_list'),
    path('download/int:file_id/', views.download_file, name='download_file'),  
    ]