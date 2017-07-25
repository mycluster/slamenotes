"""slamnotes Template Tag(s)

Custom template tag(s) for slamnotes. For more information please see:
    https://docs.djangoproject.com/en/1.10/howto/custom-template-tags/
"""

from django import template

register = template.Library()


@register.filter
def leading_zeros(integer, string_length):
    return ("%0" + str(string_length) + "d") % integer
