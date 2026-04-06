"""
Forms for the AI Movie Generator application.

This module contains Django forms for movie and series creation.
"""

from django import forms
from .models import Movie, Series

_FIELD_CLASS = (
    'w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 '
    'focus:outline-none focus:ring-2 focus:ring-purple-500 '
    'transition-all duration-200'
)
_FIELD_STYLE = (
    'background: rgba(255,255,255,0.04); '
    'border: 1px solid rgba(255,255,255,0.1); '
    'color: white; '
    'font-size: 1rem;'
)


class MovieCreationForm(forms.ModelForm):
    """Form for creating a new movie."""

    class Meta:
        model = Movie
        fields = ['title', 'genre', 'description', 'duration_minutes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE,
                'placeholder': 'Enter movie title',
            }),
            'genre': forms.Select(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE + 'cursor:pointer;',
            }),
            'description': forms.Textarea(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE + 'resize: vertical;',
                'rows': 5,
                'placeholder': 'Describe your movie plot, characters, and setting...',
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE,
                'min': 10,
                'max': 120,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['duration_minutes'].initial = 30
        self.fields['duration_minutes'].help_text = 'Target duration in minutes (10-120)'

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration < 10:
            raise forms.ValidationError('Duration must be at least 10 minutes.')
        if duration > 120:
            raise forms.ValidationError('Duration cannot exceed 120 minutes.')
        return duration


class SeriesCreationForm(forms.ModelForm):
    """Form for creating a new series."""

    class Meta:
        model = Series
        fields = ['title', 'genre', 'description', 'total_episodes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE,
                'placeholder': 'Enter series title',
            }),
            'genre': forms.Select(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE + 'cursor:pointer;',
            }),
            'description': forms.Textarea(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE + 'resize: vertical;',
                'rows': 5,
                'placeholder': 'Describe your series premise and main characters...',
            }),
            'total_episodes': forms.NumberInput(attrs={
                'class': _FIELD_CLASS,
                'style': _FIELD_STYLE,
                'min': 2,
                'max': 50,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total_episodes'].initial = 10
        self.fields['total_episodes'].help_text = 'Number of episodes in the series'

    def clean_total_episodes(self):
        episodes = self.cleaned_data.get('total_episodes')
        if episodes < 2:
            raise forms.ValidationError('Series must have at least 2 episodes.')
        if episodes > 50:
            raise forms.ValidationError('Series cannot exceed 50 episodes.')
        return episodes