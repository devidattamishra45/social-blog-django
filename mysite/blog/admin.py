from django.contrib import admin
from .models import Comment, Post


@admin.action(description="Mark selected posts as Published")
def make_published(modeladmin, request, queryset):
    queryset.update(status=Post.Status.PUBLISHED)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "author", "publish", "status"]
    list_editable = ["status"]
    list_filter = ["status", "created", "publish", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["-publish"]
    show_facets = admin.ShowFacets.ALWAYS
    actions = [make_published]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']