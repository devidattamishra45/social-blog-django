from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.db.models import Count
from .models import Post
from .forms import EmailPostForm, CommentForm
from taggit.models import Tag


def post_list(request, tag_slug=None):
    # Ordering is defined on Post.published (newest first)
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags=tag).distinct()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page", 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    draft_count = 0
    if request.user.is_authenticated and request.user.is_staff:
        draft_count = Post.objects.filter(status=Post.Status.DRAFT).count()

    return render(
        request,
        "blog/post/list.html",
        {
            "posts": posts,
            "tag": tag,
            "draft_count": draft_count,
        },
    )


def post_detail(request, id):
    post = get_object_or_404(Post.published, id=id)
    comments = post.comments.filter(active=True)

    if request.method == "POST":
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect(post.get_absolute_url())
    else:
        form = CommentForm()

    post_tags_ids = post.tags.values_list("id", flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
            "similar_posts": similar_posts,
        },
    )


def post_share(request, post_id):
    post = get_object_or_404(Post.published, id=post_id)
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} ({cd['email']}) recommends you read {post.title}"
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}'s comments: {cd['comments']}"
            )
            send_mail(
                subject,
                message,
                None,
                [cd["to"]],
            )
            sent = True
    else:
        form = EmailPostForm()

    return render(
        request,
        "blog/post/share.html",
        {"post": post, "form": form, "sent": sent},
    )


from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserRegisterForm, UserProfileForm, ProfileUpdateForm, PostForm


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("blog:post_list")
    else:
        form = UserRegisterForm()
    return render(request, "blog/registration/register.html", {"form": form})


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    # Get only published posts of this user
    posts = Post.published.filter(author=profile_user)
    return render(
        request,
        "blog/profile.html",
        {"profile_user": profile_user, "posts": posts},
    )


@login_required
def profile_edit(request):
    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("blog:profile_view", username=request.user.username)
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    return render(
        request,
        "blog/profile_edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def dashboard_view(request):
    posts = Post.objects.filter(author=request.user)
    return render(request, "blog/dashboard.html", {"posts": posts})


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # required for taggit tags
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form, "action": "Create"})


@login_required
def post_edit(request, id):
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect("blog:post_list")
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return render(
        request,
        "blog/post_form.html",
        {"form": form, "post": post, "action": "Edit"},
    )


@login_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect("blog:post_list")
    if request.method == "POST":
        post.delete()
        return redirect("blog:dashboard_view")
    return render(request, "blog/post_confirm_delete.html", {"post": post})
