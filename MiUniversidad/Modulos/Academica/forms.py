from django import forms
from .models import Pensum, Curso

class PensumForm(forms.ModelForm):
    class Meta:
        model = Pensum
        fields = ['carrera', 'curso', 'semestre']