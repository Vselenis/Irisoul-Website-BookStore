from django import forms


from .models import ContactMessage



class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields =('full_name', 'email', 'phone', 'message')
        widgets ={
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control', 'placeholder': 'Phone Number'}),
            'message': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Message'}),
        }
