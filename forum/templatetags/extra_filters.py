from django import template
from django.utils.safestring import mark_safe
import logging
import markdown
import datetime

register = template.Library()

@template.defaultfilters.stringfilter
@register.filter
def collapse(input):
    return ' '.join(input.split())


@register.filter
def can_edit_post(user, post):
    return user.can_edit_post(post)


@register.filter
def decorated_int(number, cls="thousand"):
    try:
        number = int(number)    # allow strings or numbers passed in
        if number > 999:
            thousands = float(number) / 1000.0
            format = "%.1f" if number < 99500 else "%.0f"
            s = format % thousands

            return mark_safe("<span class=\"%s\">%sk</span>" % (cls, s))
        return number
    except:
        return number

@register.filter
def or_preview(setting, request):
    if request.user.is_superuser:
        previewing = request.session.get('previewing_settings', {})
        if setting.name in previewing:
            return previewing[setting.name]

    return setting.value

@register.filter
def time_color(last_time,is_join=False):
    now = datetime.datetime.now()
    diff = now - last_time
    hours = int(diff.seconds/3600)

    if is_join:
        if diff.days < 30:
            return "warm"
        else :
            return "base"
    else:
        if diff.days > 0 or hours > 2:
            return "base"
        else:
            return "justnow"
    
@register.filter
def getval(map, key):
    return map and map.get(key, None) or None

@register.filter
def contained_in(item, container):
    return item in container

@register.filter
def static_content(content, render_mode):
    if render_mode == 'markdown':
        return mark_safe(markdown.markdown(unicode(content), ["settingsparser"]))
    elif render_mode == "html":
        return mark_safe(unicode(content))
    else:
        return unicode(content)
