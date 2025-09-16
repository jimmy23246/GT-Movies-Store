from django import template

register = template.Library()

@register.filter
def has_upvoted(review, user):
    if not user.is_authenticated:
        return False
    # review.reactions는 related_name
    return review.reactions.filter(user=user).exists()
