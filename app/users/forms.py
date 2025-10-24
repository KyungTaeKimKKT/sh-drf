from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = '__all__'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 동일하지 않습니다.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    # https://stackoverflow.com/questions/15456964/changing-password-in-django-admin/15630360#15630360
    password = ReadOnlyPasswordHashField(label= ("Password"),
                help_text= ("암호화되지 않은 비밀번호는 보안상 불가합니다."
                            "변경 시  <a href=\"../password/\" >비밀번호 변경</a> !!을 사용하세요 "
                            ))

    class Meta:
        model = User
        fields = '__all__'
        
    def clean_password(self):
        return self.initial["password"]