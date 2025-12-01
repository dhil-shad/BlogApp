from django import forms
from .models import Post, Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

# --- REGISTRATION FORM ---
class WriterRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

# --- POST FORM (UPDATED) ---
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # --- 'cover_image' IS ADDED HERE ---
        fields = ['title', 'content', 'cover_image']

# --- COMMENT FORM ---
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment...'}),
        }
        labels = {
            'body': ''
        }

class UserUpdateForm(forms.ModelForm):
    """
    Form for updating username and email.
    """
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating the profile picture.
    """
    class Meta:
        model = Profile
        fields = ['profile_pic']