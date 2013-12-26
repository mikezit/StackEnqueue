from django import template
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from forum.models import Tag, MarkedTag
from forum.templatetags import argument_parser
from forum import settings

register = template.Library()

class QuestionItemNode(template.Node):
    template = template.loader.get_template('question_list/item.html')

    def __init__(self, question, options):
        self.question = template.Variable(question)
        self.options = options

    def render(self, context):
        user= context["user"]
        user_liked_tags=[]
        question_tags=[]
        user_like_question = set()
        if user and user.is_authenticated():
            if not user.only_interesting_tag:
                user_liked_tags =  user.marked_tags.filter(user_selections__reason='good')
                question_tags =  self.question.resolve(context).tags.all()
                user_like_question = set(user_liked_tags) & set(question_tags)

        return self.template.render(template.Context({
            'question': self.question.resolve(context),
            'favorite_count': self.options.get('favorite_count', 'no') == 'yes',
            'signature_type': self.options.get('signature_type', 'lite'),
            'user_like_question' : user_like_question
        }))

class UserQuestionItemNode(QuestionItemNode):
    template = template.loader.get_template('question_list/user_item.html')

class SubscriptionItemNode(template.Node):
    template = template.loader.get_template('question_list/subscription_item.html')

    def __init__(self, subscription, question, options):
        self.question = template.Variable(question)
        self.subscription = template.Variable(subscription)
        self.options = options

    def render(self, context):
        return self.template.render(template.Context({
            'question': self.question.resolve(context),
            'subscription': self.subscription.resolve(context),
            'signature_type': self.options.get('signature_type', 'lite'),
        }))

@register.tag
def user_question_list_item(parser, token):
    tokens = token.split_contents()[1:]
    return UserQuestionItemNode(tokens[0], argument_parser(tokens[1:]))

@register.tag
def question_list_item(parser, token):
    tokens = token.split_contents()[1:]
    return QuestionItemNode(tokens[0], argument_parser(tokens[1:]))

@register.tag
def subscription_list_item(parser, token):
    tokens = token.split_contents()[1:]
    return SubscriptionItemNode(tokens[0], tokens[1], argument_parser(tokens[2:]))

@register.inclusion_tag('question_list/sort_tabs.html')
def question_sort_tabs(sort_context):
    return sort_context

@register.inclusion_tag('question_list/related_tags.html')
def question_list_related_tags(questions):
    if len(questions):
        tags = Tag.objects.filter(nodes__id__in=[q.id for q in questions]).distinct()

        if settings.LIMIT_RELATED_TAGS:
            tags = tags[:settings.LIMIT_RELATED_TAGS]

        return {'tags': tags}
    else:
        return {'tags': False}

@register.inclusion_tag('question_list/tag_selector.html', takes_context=True)
def tag_selector(context):
    request = context['request']

    if request.user.is_authenticated():
        pt = MarkedTag.objects.filter(user=request.user)
        return {
            "interesting_tag_names": pt.filter(reason='good').values_list('tag__name', flat=True),
            'ignored_tag_names': pt.filter(reason='bad').values_list('tag__name', flat=True),
            'user_authenticated': True,
            'user_id':request.user.id,
            'only_interesting_tag' : request.user.only_interesting_tag,
        }
    else:
        return {'user_authenticated': False}
