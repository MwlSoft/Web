from django import forms
from .models import Pensum, Curso, AsesoriaMensaje

class PensumForm(forms.ModelForm):
    class Meta:
        model = Pensum
        fields = ['carrera', 'curso', 'semestre']

class AsesoriaMensajeForm(forms.ModelForm):
    class Meta:
        model = AsesoriaMensaje
        fields = ['mensaje', 'profesor']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 8}),
        }