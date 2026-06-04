from django import forms

from .models import Comment


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]


from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify
from .models import Profile, Post


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell the world about yourself..."}),
        }


class PostForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False,
        help_text="Optional. Leave blank to auto-generate from title."
    )

    class Meta:
        model = Post
        fields = ["title", "slug", "body", "status", "tags"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 12,
                    "placeholder": "Write your post content here in Markdown...",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)
        if commit:
            instance.save()
            self.save_m2m()  # Important for taggit to save tags
        return instance