from django import forms
from .models import Document
import os

ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
ALLOWED_CONTENT_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]
MAX_FILE_SIZE_MB = 10

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'category', 'file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].help_text = "Leave blank to auto-detect from filename"
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            })

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError("Please select a file to upload.")

        # Check file extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"Unsupported file type '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check actual content type (harder to fake than extension alone)
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError(
                "The file's content doesn't match an allowed document type."
            )

        # Check file size
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_size_bytes:
            raise forms.ValidationError(
                f"File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
            )

        return file