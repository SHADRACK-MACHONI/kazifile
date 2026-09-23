import secrets
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from .models import Document, ShareLink, AccessLog
from .forms import DocumentUploadForm
from .utils import (
    encrypt_file, decrypt_file, guess_category, generate_qr_code_base64,
    generate_file_key, encrypt_file_key, decrypt_file_key
)
import tempfile


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'documents/landing.html')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@login_required
def dashboard_view(request):
    documents = Document.objects.filter(owner=request.user).order_by('-uploaded_at')
    return render(request, 'documents/dashboard.html', {'documents': documents})


@login_required
def upload_view(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user

            if not document.category:
                filename = request.FILES['file'].name
                document.category = guess_category(filename)

            file_key = generate_file_key()
            document.encrypted_file_key = encrypt_file_key(file_key)

            document.save()
            encrypt_file(document.file.path, file_key)
            return redirect('dashboard')
    else:
        form = DocumentUploadForm()
    return render(request, 'documents/upload.html', {'form': form})


@login_required
def delete_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, owner=request.user)
    document.file.delete()
    document.delete()
    return redirect('dashboard')


@login_required
def create_share_link(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, owner=request.user)
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(days=2)
    ShareLink.objects.create(document=document, token=token, expires_at=expires_at)

    AccessLog.objects.create(
        document=document,
        action='share_created',
        ip_address=get_client_ip(request)
    )

    full_url = request.build_absolute_uri(f'/documents/shared/{token}/')
    qr_code_data = generate_qr_code_base64(full_url)

    return render(request, 'documents/share_link.html', {
        'token': token,
        'document': document,
        'full_url': full_url,
        'qr_code_data': qr_code_data,
    })


def view_shared_document(request, token):
    share_link = get_object_or_404(ShareLink, token=token)
    if share_link.expires_at < timezone.now():
        raise Http404("This share link has expired.")

    AccessLog.objects.create(
        document=share_link.document,
        action='viewed',
        ip_address=get_client_ip(request)
    )

    file_key = decrypt_file_key(share_link.document.encrypted_file_key)
    decrypted_data = decrypt_file(share_link.document.file.path, file_key)

    temp_file = tempfile.NamedTemporaryFile()
    temp_file.write(decrypted_data)
    temp_file.seek(0)

    return FileResponse(temp_file, as_attachment=True, filename=share_link.document.title)


@login_required
def document_log_view(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, owner=request.user)
    logs = document.access_logs.all()
    return render(request, 'documents/document_log.html', {'document': document, 'logs': logs})