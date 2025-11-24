from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import FileResponse
from django.db.models import Sum
from django.contrib import messages
from .models import File
from .forms import FileUploadForm, FolderCreateForm
import os

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required(login_url='/login/')
def dashboard(request):
    total_files = File.objects.filter(user=request.user, is_folder=False).count()
    total_size = File.objects.filter(user=request.user, is_folder=False).aggregate(Sum('size'))['size__sum'] or 0
    recent_files = File.objects.filter(user=request.user, is_folder=False).order_by('-uploaded_at')[:5]
    
    context = {
        'total_files': total_files,
        'total_size': round(total_size / (1024*1024), 2),
        'recent_files': recent_files,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='/login/')
def file_list(request):
    # Корневая директория - файлы и папки без parent_folder
    files = File.objects.filter(user=request.user, is_folder=False, parent_folder__isnull=True)
    folders = File.objects.filter(user=request.user, is_folder=True, parent_folder__isnull=True)
    
    context = {
        'files': files,
        'folders': folders,
        'current_folder': None,
    }
    return render(request, 'files.html', context)

@login_required(login_url='/login/')
def folder_view(request, folder_id):
    folder = get_object_or_404(File, id=folder_id, user=request.user, is_folder=True)
    files = File.objects.filter(user=request.user, is_folder=False, parent_folder=folder)
    folders = File.objects.filter(user=request.user, is_folder=True, parent_folder=folder)
    
    context = {
        'files': files,
        'folders': folders,
        'current_folder': folder,
    }
    return render(request, 'files.html', context)

@login_required(login_url='/login/')
def upload_file(request):
    current_folder_id = request.GET.get('folder')
    current_folder = None
    if current_folder_id:
        current_folder = get_object_or_404(File, id=current_folder_id, user=request.user, is_folder=True)
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            uploaded_count = 0
            
            for file in files:
                if file.size > 100 * 1024 * 1024:
                    messages.error(request, f'Файл {file.name} слишком большой (макс. 100MB)')
                    continue
                
                # Проверяем, нет ли файла с таким именем
                existing_file = File.objects.filter(
                    user=request.user,
                    name=file.name,
                    is_folder=False,
                    parent_folder=current_folder
                ).exists()
                
                if existing_file:
                    messages.warning(request, f'Файл {file.name} уже существует и будет пропущен')
                    continue
                
                file_instance = File(
                    user=request.user,
                    file=file,
                    name=file.name,
                    size=file.size,
                    parent_folder=current_folder
                )
                file_instance.save()
                uploaded_count += 1
            
            if uploaded_count > 0:
                messages.success(request, f'Успешно загружено {uploaded_count} файл(ов)')
            
            if current_folder:
                return redirect('folder_view', folder_id=current_folder.id)
            else:
                return redirect('file_list')
    else:
        form = FileUploadForm()
    
    context = {
        'form': form,
        'current_folder': current_folder,
    }
    return render(request, 'upload.html', context)

@login_required(login_url='/login/')
def create_folder(request):
    current_folder_id = request.GET.get('folder')
    current_folder = None
    if current_folder_id:
        current_folder = get_object_or_404(File, id=current_folder_id, user=request.user, is_folder=True)
    
    if request.method == 'POST':
        form = FolderCreateForm(request.POST)
        if form.is_valid():
            folder_name = form.cleaned_data['name']
            
            # Проверяем, нет ли папки с таким именем
            existing_folder = File.objects.filter(
                user=request.user,
                name=folder_name,
                is_folder=True,
                parent_folder=current_folder
            ).exists()
            
            if existing_folder:
                messages.error(request, f'Папка "{folder_name}" уже существует')
            else:
                File.objects.create(
                    user=request.user,
                    name=folder_name,
                    is_folder=True,
                    parent_folder=current_folder
                )
                messages.success(request, f'Папка "{folder_name}" создана')
            
            if current_folder:
                return redirect('folder_view', folder_id=current_folder.id)
            else:
                return redirect('file_list')
    
    return redirect('file_list')

@login_required(login_url='/login/')
def delete_file(request, file_id):
    file = get_object_or_404(File, id=file_id, user=request.user)
    parent_folder = file.parent_folder
    
    if request.method == 'POST':
        file_name = file.name
        file.delete()
        messages.success(request, f'"{file_name}" удален')
        
        if parent_folder:
            return redirect('folder_view', folder_id=parent_folder.id)
        else:
            return redirect('file_list')
    
    return render(request, 'confirm_delete.html', {'file': file})

@login_required(login_url='/login/')
def download_file(request, file_id):
    file = get_object_or_404(File, id=file_id, user=request.user, is_folder=False)
    if file.file:
        try:
            response = FileResponse(
                file.file.open('rb'),
                as_attachment=True,
                filename=file.name
            )
            return response
        except Exception as e:
            messages.error(request, f'Ошибка при скачивании: {str(e)}')
            return redirect('file_list')
    else:
        messages.error(request, 'Файл не найден')
        return redirect('file_list')