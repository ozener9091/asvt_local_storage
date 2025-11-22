from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import DocumentForm
from .models import Document
import os


# Create your views here.
def upload_file(request):
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('file_list')
    else:
        form = DocumentForm()
        return render(request, '/storage/upload.html', {'form': form})


def file_list(request):
    
    documents = Document.objects.all()
    return render(request, 'storage/file_list.html', {'documents': documents})


def download_file(request, file_id):
    
    document = get_object_or_404(Document, id=file_id)
    file_path = document.file.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = 'inline;filename=' + os.path.basename(file_path)
            return response
    else:
        raise Http404
    
    
        