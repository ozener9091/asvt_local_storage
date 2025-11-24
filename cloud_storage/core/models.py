from django.db import models
from django.contrib.auth.models import User
import os
import uuid

def user_directory_path(instance, filename):
    if instance.parent_folder:
        return f'user_{instance.user.id}/{instance.parent_folder.name}/{filename}'
    return f'user_{instance.user.id}/{filename}'

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path, null=True, blank=True)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_folder = models.BooleanField(default=False)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_files')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            if self.file:
                self.name = os.path.basename(self.file.name)
        if self.file and not self.size and not self.is_folder:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_folder:
            # Удаляем все дочерние файлы и папки
            child_files = File.objects.filter(parent_folder=self)
            for child in child_files:
                child.delete()
        elif self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    @property
    def children(self):
        """Все дочерние элементы (файлы и папки)"""
        return File.objects.filter(parent_folder=self)

    @property
    def child_folders(self):
        """Только дочерние папки"""
        return File.objects.filter(parent_folder=self, is_folder=True)

    @property
    def child_files(self):
        """Только дочерние файлы"""
        return File.objects.filter(parent_folder=self, is_folder=False)

    def get_files_count(self):
        """Количество файлов в папке (рекурсивно)"""
        if not self.is_folder:
            return 0
        count = self.child_files.count()
        for folder in self.child_folders:
            count += folder.get_files_count()
        return count

    def get_folder_size(self):
        """Размер папки (рекурсивно)"""
        if not self.is_folder:
            return self.size
        total_size = self.child_files.aggregate(models.Sum('size'))['size__sum'] or 0
        for folder in self.child_folders:
            total_size += folder.get_folder_size()
        return total_size