from django import forms
from captcha.fields import CaptchaField


class ContactForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=255)
    email = forms.EmailField(label='E-mail')
    content = forms.CharField(label='Контент', widget=forms.Textarea(attrs={'rows':10, 'cols':50}))
    captcha = CaptchaField()