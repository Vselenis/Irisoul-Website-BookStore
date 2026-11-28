from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage

MAX_PDF_SIZE = 50 * 1024 * 1024


def protected_storage():
    return FileSystemStorage(location=settings.PROTECTED_MEDIA_ROOT, base_url='/protected/')


def validate_pdf(file):
    if file.size > MAX_PDF_SIZE:
        raise ValidationError('The PDF file must be 50 MB or smaller.')
    position = file.tell() if hasattr(file, 'tell') else 0
    file.seek(0)
    header = file.read(5)
    file.seek(position)
    if header != b'%PDF-':
        raise ValidationError('Upload a valid PDF file.')
