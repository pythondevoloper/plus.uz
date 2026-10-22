from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, Review


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Parol", min_length=8,
                                widget=forms.PasswordInput(attrs={"placeholder": "Kamida 8 ta belgi"}))
    password2 = forms.CharField(label="Parolni takrorlang",
                                widget=forms.PasswordInput(attrs={"placeholder": "Parolni qayta kiriting"}))

    class Meta:
        model = CustomUser
        fields = ["full_name", "email", "phone_number"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Ism Familiya"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@misol.uz"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu email bilan foydalanuvchi allaqachon ro'yxatdan o'tgan.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar bir-biriga mos kelmadi.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email",
                                widget=forms.EmailInput(attrs={"placeholder": "email@misol.uz", "autofocus": True}))
    password = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={"placeholder": "Parolingiz"}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["full_name", "phone_number", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Mahsulot haqida fikringiz (ixtiyoriy)..."}),
        }
