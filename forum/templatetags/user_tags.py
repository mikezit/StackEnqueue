from django import template
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
import logging

register = template.Library()

class UserSignatureNode(template.Node):
    template = template.loader.get_template('users/signature.html')

    def __init__(self, user, format):
        self.user = template.Variable(user)
        self.format = template.Variable(format)

    def render(self, context):
        return self.template.render(template.Context({
        'user': self.user.resolve(context),
        'format': self.format.resolve(context)
        }))

@register.tag
def user_signature(parser, token):
    try:
        tag_name, user, format = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return UserSignatureNode(user, format)


class ActivityNode(template.Node):
    template = template.loader.get_template('users/activity.html')

    def __init__(self, activity, viewer,userpage=False):
        self.activity = template.Variable(activity)
        self.viewer = template.Variable(viewer)
        self.userpage = userpage

    def render(self, context):
        try:
            action = self.activity.resolve(context).leaf
            viewer = self.viewer.resolve(context)
            if self.userpage:
                target = mark_safe(action.target(viewer))
                return self.template.render(template.Context(dict(action=action,target=target)))
            else:
                describe = mark_safe(action.describe(viewer))
                return self.template.render(template.Context(dict(action=action, describe=describe)))
        except Exception, e:
            import traceback
            msg = "Error in action describe: \n %s" % (
                traceback.format_exc()
            )
            logging.error(msg)

class UserActivityNode(ActivityNode):
    template = template.loader.get_template('users/user_activity.html')

class UserReputationNode(template.Node):
    template = template.loader.get_template('users/user_reputation_item.html')
    def __init__(self, rep,action, viewer,userpage=False):
        self.action= template.Variable(action)
        self.rep = template.Variable(rep)
        self.viewer = template.Variable(viewer)
        self.userpage = userpage

    def render(self, context):
        try:
            action = self.action.resolve(context).leaf
            rep = self.rep.resolve(context)
            viewer = self.viewer.resolve(context)
            target = mark_safe(action.target(viewer))
            return self.template.render(template.Context(dict(action=action, target=target,rep=rep)))
        except Exception, e:
            import traceback
            msg = "Error in action describe: \n %s" % (
                traceback.format_exc()
            )
            logging.error(msg)

@register.tag
def activity_desc(parser, token):
    try:
        tag_name, activity, viewer = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return UserActivityNode(activity, viewer)

@register.tag
def activity_item(parser, token):
    try:
        tag_name, activity, viewer = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return ActivityNode(activity, viewer)

@register.tag
def user_activity_item(parser, token):
    try:
        tag_name, activity, viewer = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return UserActivityNode(activity, viewer,True)

@register.tag
def user_reputation_item(parser, token):
    try:
        tag_name, rep,action, viewer = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return UserReputationNode(rep, action,viewer,True)


@register.tag
def flagged_item(parser, token):
    try:
        tag_name, post, viewer = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return ActivityNode(post, viewer)


@register.inclusion_tag('users/menu.html')
def user_menu(viewer, user):
    return dict(viewer=viewer, user=user)

