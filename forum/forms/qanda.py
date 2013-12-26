# encoding:utf-8
import re
import Image
from datetime import date
from django import forms
from forum.models import *
from django.utils.translation import ugettext as _
from django.contrib.humanize.templatetags.humanize import apnumber

from django.utils.safestring import mark_safe
from general import NextUrlField, UserNameField, SetPasswordForm
from forum import settings

from forum.modules import call_all_handlers

import logging


class TitleField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(TitleField, self).__init__(*args, **kwargs)
        self.required = True
        self.max_length = 255
        self.widget = forms.TextInput(attrs={'size' : 70, 'autocomplete' : 'off', 'maxlength' : self.max_length,'style': "width:610px;border: 1px solid #999;",'placeholder':_('please enter a descriptive title for your question')})
        self.label  = _('title')
        self.help_text = _('please enter a descriptive title for your question')
        self.initial = ''

    def clean(self, value):
        if len(value) < settings.FORM_MIN_QUESTION_TITLE:
            raise forms.ValidationError(_('title must be must be at least %s characters') % settings.FORM_MIN_QUESTION_TITLE)

        return value

class EditorField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(EditorField, self).__init__(*args, **kwargs)
        self.widget = forms.Textarea(attrs={'id':'editor'})
        self.label  = _('content')
        self.help_text = u''
        self.initial = ''


class TagTitleField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(TagTitleField, self).__init__(*args, **kwargs)
        self.required = True
        self.max_length = 1000
        self.widget = forms.Textarea(attrs={'id':'editor-tag','rows':'4','maxlength' : self.max_length,'style':"width:660px"})
        self.label  = _('Excerpt')
        self.help_text = _('please enter a descriptive title for the tag')
        self.initial = ''

    def clean(self, value):
        if not bool(settings.FORM_EMPTY_QUESTION_BODY) and (len(re.sub('[ ]{2,}', ' ', value)) < settings.FORM_MIN_QUESTION_BODY):
            raise forms.ValidationError(_('question content must be at least %s characters') % settings.FORM_MIN_QUESTION_BODY)

        return value

class TagEditorField(EditorField):
    def __init__(self, *args, **kwargs):
        super(TagEditorField, self).__init__(*args, **kwargs)
        self.required = not bool(settings.FORM_EMPTY_TAG_BODY)

    def clean(self, value):
        if value and (len(re.sub('[ ]{2,}', ' ', value)) < settings.FORM_MIN_TAG_BODY):
            raise forms.ValidationError(_('tag content must be at least %s characters') % settings.FORM_MIN_TAG_BODY)
        return value

class QuestionEditorField(EditorField):
    def __init__(self, *args, **kwargs):
        super(QuestionEditorField, self).__init__(*args, **kwargs)
        self.required = not bool(settings.FORM_EMPTY_QUESTION_BODY)


    def clean(self, value):
        if not bool(settings.FORM_EMPTY_QUESTION_BODY) and (len(re.sub('[ ]{2,}', ' ', value)) < settings.FORM_MIN_QUESTION_BODY):
            raise forms.ValidationError(_('question content must be at least %s characters') % settings.FORM_MIN_QUESTION_BODY)

        return value

class AnswerEditorField(EditorField):
    def __init__(self, *args, **kwargs):
        super(AnswerEditorField, self).__init__(*args, **kwargs)
        self.required = True

    def clean(self, value):
        if len(re.sub('[ ]{2,}', ' ', value)) < settings.FORM_MIN_QUESTION_BODY:
            raise forms.ValidationError(_('answer content must be at least %s characters') % settings.FORM_MIN_QUESTION_BODY)

        return value




class TagNamesField(forms.CharField):
    def __init__(self, user=None, *args, **kwargs):
        super(TagNamesField, self).__init__(*args, **kwargs)
        self.required = True
        self.widget = forms.TextInput(attrs={'id':'tagnames','name':'tagnames','type':'text','size' : 60, 'autocomplete' : 'off','style':"width:660px"})
        self.max_length = 255
        self.label  = _('tags')
        self.help_text = _('Tags are short keywords, with no spaces within. At least %(min)s and up to %(max)s tags can be used.') % {
            'min': settings.FORM_MIN_NUMBER_OF_TAGS, 'max': settings.FORM_MAX_NUMBER_OF_TAGS       }
        self.initial = ''
        self.user = user

    def clean(self, value):
        value = super(TagNamesField, self).clean(value)
        data = value.strip().lower()

        split_re = re.compile(r'[ ,]+')
        #list = {}
        #for tag in split_re.split(data):
        #    list[tag] = tag
        tag_list=split_re.split(data)
        if len(tag_list) > settings.FORM_MAX_NUMBER_OF_TAGS or len(tag_list) < settings.FORM_MIN_NUMBER_OF_TAGS:
            raise forms.ValidationError(_('please use between %(min)s and %(max)s tags') % { 'min': settings.FORM_MIN_NUMBER_OF_TAGS, 'max': settings.FORM_MAX_NUMBER_OF_TAGS})

        list_temp = []
        tagname_re = re.compile(r'^[\w#+\.-]+$', re.UNICODE)
        for tag in tag_list:
            if len(tag) > settings.FORM_MAX_LENGTH_OF_TAG or len(tag) < settings.FORM_MIN_LENGTH_OF_TAG:
                raise forms.ValidationError(_('please use between %(min)s and %(max)s characters in you tags') % { 'min': settings.FORM_MIN_LENGTH_OF_TAG, 'max': settings.FORM_MAX_LENGTH_OF_TAG})
            if not tagname_re.match(tag):
                raise forms.ValidationError(_('please use following characters in tags: letters , numbers, and characters \'.-_\''))
            # only keep one same tag
            if tag not in list_temp and len(tag.strip()) > 0:
                list_temp.append(tag)

        if settings.LIMIT_TAG_CREATION and not self.user.can_create_tags():
            existent = Tag.objects.filter(name__in=list_temp).values_list('name', flat=True)

            if len(existent) < len(list_temp):
                unexistent = [n for n in list_temp if not n in existent]
                raise forms.ValidationError(_("You don't have enough reputation to create new tags. The following tags do not exist yet: %s") %
                        ', '.join(unexistent))


        return u' '.join(list_temp)

class WikiField(forms.BooleanField):
    def __init__(self, disabled=False, *args, **kwargs):
        super(WikiField, self).__init__(*args, **kwargs)
        self.required = False
        self.label  = _('community wiki')
        self.help_text = _('if you choose community wiki option, the question and answer do not generate points and name of author will not be shown')
        if disabled:
            self.widget=forms.CheckboxInput(attrs={'disabled': "disabled"})
    def clean(self,value):
        return value

class EmailNotifyField(forms.BooleanField):
    def __init__(self, *args, **kwargs):
        super(EmailNotifyField, self).__init__(*args, **kwargs)
        self.required = False
        self.widget.attrs['class'] = 'nomargin'

class SummaryField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(SummaryField, self).__init__(*args, **kwargs)
        self.required = False
        self.widget = forms.TextInput(attrs={'size' : 50, 'autocomplete' : 'off','style':"width:660px"})
        self.max_length = 300
        self.label  = _('update summary:')
        self.help_text = _('enter a brief summary of your revision (e.g. fixed spelling, grammar, improved style, this field is optional)')


class FeedbackForm(forms.Form):
    message = forms.CharField(label=_('Your message:'), max_length=800,widget=forms.Textarea(attrs={'cols':60}))
    next = NextUrlField()

    def __init__(self, user, *args, **kwargs):
        super(FeedbackForm, self).__init__(*args, **kwargs)
        if not user.is_authenticated():
            self.fields['name'] = forms.CharField(label=_('Your name:'), required=False)
            self.fields['email'] = forms.EmailField(label=_('Email (not shared with anyone):'), required=True)

class AskForm(forms.Form):
    title  = TitleField()
    text   = QuestionEditorField()

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(AskForm, self).__init__(data, *args, **kwargs)

        self.fields['tags']   = TagNamesField(user)
        
        if int(user.reputation) < settings.CAPTCHA_IF_REP_LESS_THAN and not (user.is_superuser or user.is_staff):
            spam_fields = call_all_handlers('create_anti_spam_field')
            if spam_fields:
                spam_fields = dict(spam_fields)
                for name, field in spam_fields.items():
                    self.fields[name] = field

                self._anti_spam_fields = spam_fields.keys()
            else:
                self._anti_spam_fields = []

        if settings.WIKI_ON:
            self.fields['wiki'] = WikiField()

class AnswerForm(forms.Form):
    text   = AnswerEditorField()
    wiki   = WikiField()

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(AnswerForm, self).__init__(data, *args, **kwargs)
        
        if int(user.reputation) < settings.CAPTCHA_IF_REP_LESS_THAN and not (user.is_superuser or user.is_staff):
            spam_fields = call_all_handlers('create_anti_spam_field')
            if spam_fields:
                spam_fields = dict(spam_fields)
                for name, field in spam_fields.items():
                    self.fields[name] = field

                self._anti_spam_fields = spam_fields.keys()
            else:
                self._anti_spam_fields = []

        if settings.WIKI_ON:
            self.fields['wiki'] = WikiField()

class RetagQuestionForm(forms.Form):
    tags   = TagNamesField()
    # initialize the default values
    def __init__(self, question, *args, **kwargs):
        super(RetagQuestionForm, self).__init__(*args, **kwargs)
        self.fields['tags'].initial = question.tagnames

class GravatarSelectForm(forms.Form):
    gravatar = forms.BooleanField(widget=forms.CheckboxInput(attrs={'id':'email_gravatar'}),required=False)
    local_gravatar = forms.BooleanField(widget=forms.CheckboxInput(attrs={'id':'local_gravatar'}),required=False)
    weibo_gravatar = forms.BooleanField(widget=forms.CheckboxInput(attrs={'id':'weibo_gravatar'}),required=False)
    def __init__(self,user, *args, **kwargs):
        super(GravatarSelectForm, self).__init__(*args, **kwargs)
        if not user.local_gravatar and not user.weibo_gravatar:
            self.fields["gravatar"].initial=True
            self.fields["gravatar"].widget.attrs["disabled"]="disabled"
        elif user.use_local_gravatar:
            self.fields["local_gravatar"].initial=True
        elif user.use_weibo_gravatar:
            self.fields["weibo_gravatar"].initial=True
        else:
            self.fields["gravatar"].initial=True        

class RevisionForm(forms.Form):
    """
    Lists revisions of a Question or Answer
    """
    revision = forms.ChoiceField(widget=forms.Select(attrs={'style' : 'width:600px;margin: 5px 0px;'}))

    def __init__(self, post, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)

        revisions = post.revisions.exclude(suggest_status="pendding").values_list('revision', 'author__username', 'revised_at', 'summary','suggested').order_by('-revised_at')

        date_format = '%Y %m/%d %H:%M:%S'
        rev_list = []
        
        for r in revisions:
            if r[4]:
                action = _("suggest")
            else:
                action = _("edit")

            rev_list.append( (r[0], u'%s - %s (%s) %s %s' % (r[0], unicode(r[1],"utf-8"), r[2].strftime(date_format),action, r[3])))

        self.fields['revision'].choices = rev_list

        self.fields['revision'].initial = post.active_revision.revision



class EditTagForm(forms.Form):
    title =  TagTitleField()
    text = TagEditorField()
    sponsor_tag_img = forms.URLField(label=_('sponsor img'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    

    def __init__(self,tag,user,revision=None,*args, **kwargs):
        super(EditTagForm, self).__init__(*args, **kwargs)

        if revision is None:
            if tag.pendding_suggestion and tag.pendding_suggestion.author == user:
                revision = tag.pendding_suggestion
            elif tag.active_revision is not None:
                revision = tag.active_revision
            else:
                revision = tag

        if revision is not None:
            self.fields['title'].initial = revision.about
            self.fields['text'].initial = revision.detail

        self.fields['sponsor_tag_img'].initial = tag.sponsor_tag_img
 
    def clean_image(self):
        return self.cleaned_data['sponsor_tag_img']

class EditQuestionForm(forms.Form):
    title  = TitleField()
    text   = QuestionEditorField()
    summary = SummaryField()

    def __init__(self, question, user, revision=None, *args, **kwargs):
        super(EditQuestionForm, self).__init__(*args, **kwargs)

        if revision is None:
            if question.pendding_suggestion and question.pendding_suggestion.author == user:
                revision = question.pendding_suggestion
            else:
                revision = question.active_revision

        self.fields['title'].initial = revision.title
        self.fields['text'].initial = revision.body

        self.fields['tags'] = TagNamesField(user)
        self.fields['tags'].initial = revision.tagnames

        if int(user.reputation) < settings.CAPTCHA_IF_REP_LESS_THAN and not (user.is_superuser or user.is_staff):
            spam_fields = call_all_handlers('create_anti_spam_field')
            if spam_fields:
                spam_fields = dict(spam_fields)
                for name, field in spam_fields.items():
                    self.fields[name] = field

                self._anti_spam_fields = spam_fields.keys()
            else:
                self._anti_spam_fields = []

        if settings.WIKI_ON:
            self.fields['wiki'] = WikiField(disabled=(question.nis.wiki and not user.can_cancel_wiki(question)), initial=question.nis.wiki)

class EditAnswerForm(forms.Form):
    text = AnswerEditorField()
    summary = SummaryField()

    def __init__(self, answer, user, revision=None, *args, **kwargs):
        super(EditAnswerForm, self).__init__(*args, **kwargs)

        if revision is None:
            if answer.pendding_suggestion and answer.pendding_suggestion.author == user:
                revision = answer.pendding_suggestion
            else:
                revision = answer.active_revision

        self.fields['text'].initial = revision.body

        if int(user.reputation) < settings.CAPTCHA_IF_REP_LESS_THAN and not (user.is_superuser or user.is_staff):
            spam_fields = call_all_handlers('create_anti_spam_field')
            if spam_fields:
                spam_fields = dict(spam_fields)
                for name, field in spam_fields.items():
                    self.fields[name] = field

                self._anti_spam_fields = spam_fields.keys()
            else:
                self._anti_spam_fields = []
        
        if settings.WIKI_ON:
            self.fields['wiki'] = WikiField(disabled=(answer.nis.wiki and not user.can_cancel_wiki(answer)), initial=answer.nis.wiki)

class UserAboutField(EditorField):
    def __init__(self, *args, **kwargs):
        super(UserAboutField, self).__init__(*args, **kwargs)
        self.required = False
        self.label=_('Profile')

    def clean(self, value):
        return value

class EditUserForm(forms.Form):
    email = forms.EmailField(label=u'Email', help_text=_('this email does not have to be linked to gravatar'), required=True, max_length=75, widget=forms.TextInput(attrs={'size' : 35}))
    display_name = forms.CharField(label=_('Screen name'), required=True, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))    
    realname = forms.CharField(label=_('Real name'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    website = forms.URLField(label=_('Website'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    city = forms.CharField(label=_('Location'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    birthday = forms.DateField(label=_('Date of birth'), help_text=_('will not be shown, used to calculate age, format: YYYY-MM-DD'), required=False, widget=forms.TextInput(attrs={'size' : 35}))
    about = UserAboutField()#forms.CharField(label=_('Profile'), required=False, widget=forms.Textarea(attrs={'cols' : 60,'id':'editor'}))

    def __init__(self, user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        if len(user.display_name) is 0:
            self.fields['display_name'].initial = user.username
        else:
            self.fields['display_name'].initial = user.display_name

        self.fields['email'].initial = user.email
        self.fields['realname'].initial = user.real_name
        self.fields['website'].initial = user.website
        self.fields['city'].initial = user.location

        if user.date_of_birth is not None:
            self.fields['birthday'].initial = user.date_of_birth

        self.fields['about'].initial = user.about
        self.user = user

    def clean_display_name(self):
        if self.user.display_name != self.cleaned_data['display_name']:
            if len(self.cleaned_data['display_name']) < settings.MIN_DISPLAY_NAME_LENGTH:
                raise forms.ValidationError(_('user name is to short, please use at least %d characters') % settings.MIN_DISPLAY_NAME_LENGTH)
            
        return self.cleaned_data['display_name']


    def clean_email(self):
        if self.user.email != self.cleaned_data['email']:
            if settings.EMAIL_UNIQUE == True:
                if 'email' in self.cleaned_data:
                    from forum.models import User
                    try:
                        User.objects.get(email = self.cleaned_data['email'])
                    except User.DoesNotExist:
                        return self.cleaned_data['email']
                    except User.MultipleObjectsReturned:
                        logging.error("Found multiple users sharing the same email: %s" % self.cleaned_data['email'])
                        
                    raise forms.ValidationError(_('this email has already been registered, please use another one'))
        return self.cleaned_data['email']
        

NOTIFICATION_CHOICES = (
    ('i', _('Instantly')),
    #('d', _('Daily')),
    #('w', _('Weekly')),
    ('n', _('No notifications')),
)

class SubscriptionSettingsForm(forms.ModelForm):
    enable_notifications = forms.BooleanField(widget=forms.HiddenInput, required=False)
    member_joins = forms.ChoiceField(widget=forms.RadioSelect, choices=NOTIFICATION_CHOICES)
    new_question = forms.ChoiceField(widget=forms.RadioSelect, choices=NOTIFICATION_CHOICES)
    new_question_watched_tags = forms.ChoiceField(widget=forms.RadioSelect, choices=NOTIFICATION_CHOICES)
    subscribed_questions = forms.ChoiceField(widget=forms.RadioSelect, choices=NOTIFICATION_CHOICES)

    class Meta:
        model = SubscriptionSettings

class UserPreferencesForm(forms.Form):
    sticky_sorts = forms.BooleanField(required=False, initial=False)

class OriginalForm(forms.ModelForm):
    """
    Form class for uplaod images will be cropped
    """

    class Meta:
        model = Original

class CroppedForm(forms.ModelForm):
    """
    Form class for crop images
    """

    def __init__(self, *args, **kwargs):
        """
        The class contructor. Changes ``original`` widget field type to hidden
        """
        super(CroppedForm, self).__init__(*args, **kwargs)

        #for i in ['original', 'x', 'y', 'w', 'h']:
        #    self.fields[i].widget = forms.HiddenInput()
        self.fields['original'].widget = forms.HiddenInput()

    def _dimension_clean(self, field, key, offset='not_exists'):
        """
        Form helper. Validates for cropped area offset left, offset top,
        area width and  height values.
        """
        value  = self.cleaned_data.get(key, 0)
        offset  = self.cleaned_data.get(offset, 0)
        original = self.cleaned_data.get('original')

        if not original:
            return value

        if value + offset > getattr(original, 'image_%s' % field):
            raise forms.ValidationError, _('Value exceeds picture dimension')

        return value

    def clean_x(self):
        """
        Validates for cropped area offset left
        """
        return self._dimension_clean('width', 'x')

    def clean_y(self):
        """
        Validates for cropped area offset top
        """
        return self._dimension_clean('height', 'y')

    def clean_w(self):
        """
        Validates for cropped area width
        """
        return self._dimension_clean('width', 'w', 'x')

    def clean_h(self):
        """
        Validates for cropped area height
        """
        return self._dimension_clean('height', 'h', 'y')

    class Meta:
        model = Cropped
