from django import forms
from django.core.exceptions import ValidationError

from .models import Post, Comment


class AddPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'photo', 'content', 'is_published']
        widgets = {
            'title': forms.TextInput(),
            'content': forms.Textarea()
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) > 50:
            raise ValidationError("Длина не должна превышать 50 сиволов.")
        return title
    

class AddCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишите ваш комментарий...'}),
        }
        labels = {
            'content': '',
        }