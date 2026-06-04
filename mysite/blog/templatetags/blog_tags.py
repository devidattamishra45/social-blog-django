import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

from ..models import Post

register = template.Library()


@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag("blog/post/latest_posts.html")
def show_latest_posts(count=5):
    latest_posts = Post.published.all()[:count]
    return {"latest_posts": latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count("comments")).order_by(
        "-total_comments"
    )[:count]


@register.filter(name="markdown")
def markdown_format(text):
    if text is None:
        return ""
    return mark_safe(
        markdown.markdown(str(text), extensions=["extra", "nl2br"])
    )


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    request = context.get("request")
    if request is None:
        q = {}
    else:
        q = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            q.pop(key, None)
        else:
            q[key] = value
    if not q:
        return ""
    return "?" + q.urlencode()
