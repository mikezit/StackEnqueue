# encoding:utf-8
import datetime
import logging
from urllib import unquote
from forum import settings as django_settings
from forum.settings.privilege import *
from forum.settings.minrep import *
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponsePermanentRedirect
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext
from django import template
from django.utils.html import *
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.db.models import Q, Count
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.views.decorators.cache import cache_page
from django.utils.http import urlquote  as django_urlquote
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from forum.utils.html import sanitize_html, hyperlink
from forum.utils.diff import textDiff as htmldiff2
from forum.utils.diff2 import textDiff as htmldiff
from forum.utils.diff2 import tagsDiff as tagsdiff
from forum.utils import pagination
from forum.templatetags.extra_tags import tags_html
from forum.forms import *
from forum.models import *
from forum.forms import get_next_url
from forum.actions import QuestionViewAction,TagViewAction
from forum.http_responses import HttpResponseUnauthorized
from forum.feed import RssQuestionFeed, RssAnswerFeed
from forum.utils.pagination import generate_uri
from forum.templatetags.extra_filters import static_content
import decorators
from random import randint

class HottestQuestionsSort(pagination.SortBase):
    def apply(self, questions):
        return questions.annotate(new_child_count=Count('all_children')).filter(
                all_children__added_at__gt=datetime.datetime.now() - datetime.timedelta(days=1)).order_by('-new_child_count')


class QuestionListPaginatorContext(pagination.PaginatorContext):
    def __init__(self, id='QUESTIONS_LIST', prefix='', default_pagesize=15):
        super (QuestionListPaginatorContext, self).__init__(id, sort_methods=(
            ('active', pagination.SimpleSort(_('active'), '-last_activity_at', _("Most <strong>recently updated</strong> questions"))),
            ('newest', pagination.SimpleSort(_('newest'), '-added_at', _("most <strong>recently asked</strong> questions"))),
            ('hottest', HottestQuestionsSort(_('hottest'), _("most <strong>active</strong> questions in the last 24 hours</strong>"))),
            ('mostvoted', pagination.SimpleSort(_('most voted'), '-score', _("most <strong>voted</strong> questions"))),
        ), pagesizes=(15, 20, 30), default_pagesize=default_pagesize, prefix=prefix)

class AnswerSort(pagination.SimpleSort):
    def apply(self, answers):
        if not settings.DISABLE_ACCEPTING_FEATURE:
            return answers.order_by(*(['-marked'] + list(self._get_order_by())))
        else:
            return super(AnswerSort, self).apply(answers)

class AnswerPaginatorContext(pagination.PaginatorContext):
    def __init__(self, id='ANSWER_LIST', prefix='', default_pagesize=10):
        super (AnswerPaginatorContext, self).__init__(id, sort_methods=(
            (_('oldest'), AnswerSort(_('oldest answers'), 'added_at', _("oldest answers will be shown first"))),
            (_('newest'), AnswerSort(_('newest answers'), '-added_at', _("newest answers will be shown first"))),
            (_('votes'), AnswerSort(_('popular answers'), ('-score', 'added_at'), _("most voted answers will be shown first"))),
        ), default_sort=_('votes'), pagesizes=(5, 10, 20), default_pagesize=default_pagesize, prefix=prefix)

class TagPaginatorContext(pagination.PaginatorContext):
    def __init__(self):
        super (TagPaginatorContext, self).__init__('TAG_LIST', sort_methods=(
            ('name', pagination.SimpleSort(_('by name'), 'name', _("sorted alphabetically"))),
            ('used', pagination.SimpleSort(_('by popularity'), '-used_count', _("sorted by frequency of tag use"))),
        ), default_sort=_('used'), pagesizes=(36, 36, 120))
    

def feed(request):
    return RssQuestionFeed(
                request,
                Question.objects.filter_state(deleted=False).order_by('-last_activity_at'),
                settings.APP_TITLE + _(' - ')+ _('latest questions'),
                settings.APP_DESCRIPTION)(request)

@decorators.render('index.html')
def index(request):
    paginator_context = QuestionListPaginatorContext()
    paginator_context.base_path = '/'

    known_tip = None
    if len(settings.KNOWN_TIPS_PAGE_TEXT.strip()) > 0 :
        known_tips = settings.KNOWN_TIPS_PAGE_TEXT.split("|")
        known_tip = known_tips[randint(0,len(known_tips)-1)]

    now = datetime.datetime.now()
    #if request.path == '/' :
        #questions = Question.objects.filter(last_activity_at__gte=datetime.datetime(now.year,now.month-3,now.day)) # first index page just now last three month's data , i think i will speed up 
    #else:
    questions = Question.objects.all()

    if request.user.is_authenticated():
        good_tags = [t.tag.id for t in request.user.tag_selections.filter(reason="good")]
        if request.user.only_interesting_tag and len(good_tags) != 0 :
            questions = questions.filter(tags__id__in=good_tags)
        else:
            questions = questions.exclude(tags__id__in=[t.tag.id for t in request.user.tag_selections.filter(reason="bad")])

    return question_list(request,
                         questions,
                         page_title=_("New Questions"),
                         base_path=reverse('questions'),
                         feed_url=reverse('latest_questions_feed'),
                         paginator_context=paginator_context,
                         is_home_page=True,
                         known_tip=known_tip.strip())

@decorators.render('questions.html', 'unanswered', _('unanswered'), weight=400)
def unanswered(request):
    return question_list(request,
                         Question.objects.exclude(id__in=Question.objects.filter(children__marked=True).distinct()),
                         _('open questions without an accepted answer'),
                         None,
                         _("Unanswered Questions"))

@decorators.render('questions.html', 'questions', _('questions'), weight=0)
def questions(request):
    return question_list(request, Question.objects.all(), _('questions'))

@decorators.render('questions.html')
def tag(request, tag):
    try:
        tag = Tag.active.get(name=unquote(tag))
    except Tag.DoesNotExist:
        raise Http404

    # Getting the questions QuerySet
    questions = Question.objects.filter(tags__id=tag.id)

    if request.method == "GET":
        user = request.GET.get('user', None)

        if user is not None:
            try:
                questions = questions.filter(author=User.objects.get(username=user))
            except User.DoesNotExist:
                raise Http404

    return question_list(request,
                         questions,
                         mark_safe(_('questions tagged <span class="tag">%(tag)s</span>') % {'tag': tag}),
                         None,
                         mark_safe(_('Questions Tagged With %(tag)s') % {'tag': tag}),
                         False,tag=tag)

@decorators.render('questions.html', 'questions', tabbed=False)
def user_questions(request, mode, user, slug):
    user = get_object_or_404(User, id=user)

    if mode == _('asked-by'):
        questions = Question.objects.filter(author=user)
        description = _("Questions asked by %s")
    elif mode == _('answered-by'):
        questions = Question.objects.filter(children__author=user, children__node_type='answer').distinct()
        description = _("Questions answered by %s")
    elif mode == _('subscribed-by'):
        if not (request.user.is_superuser or request.user == user):
            return HttpResponseUnauthorized(request)
        questions = user.subscriptions

        if request.user == user:
            description = _("Questions you subscribed %s")
        else:
            description = _("Questions subscribed by %s")
    else:
        raise Http404


    return question_list(request, questions,
                         mark_safe(description % hyperlink(user.get_profile_url(), user.username)),
                         page_title=description % user.username)

def allsite(request):
    _allsite=[
        #{"name":_("qigu365"),"id":"www.qigu365.com","FaviconUrl":"http://www.qigu365.com/m/default/media/images/favicon.ico","Description":_("qigu365 is a site for ask question about stock")},
        {"name":_("Stack Enqueue"),"id":"www.stackenqueue.com","FaviconUrl":"http://www.stackenqueue.com/m/default/media/images/favicon.ico","Description":_("stackenqueue is a site for ask question about programe")},
        {"name":_("Seminar Math"),"id":"www.seminarmath.com","FaviconUrl":"http://www.seminarmath.com/m/default/media/images/favicon.ico","Description":_("seminarmath is a site for ask question about math")}
        ]
    return HttpResponse(simplejson.dumps(_allsite), mimetype="application/json")

def hotquestion(request):
    tmpqs = Question.objects.filter(score__gte=1).filter(extra_count__gte=100).exclude(state_string__contains="deleted").order_by("-score");
    ques = []
    for tq in tmpqs:
        q = {}
        q["SiteId"] ="http://www.stackenqueue.com"
        q["DisplayScore"] = tq.score
        q["Id"] = tq.id
        q["Title"] = tq.title
        ques.append(q)
    return HttpResponse(simplejson.dumps(ques), mimetype="application/json")

def inbox(request):
    if not request.user.is_authenticated():
        return HttpResponse(simplejson.dumps("nlogin"), mimetype="application/json")
        
    actions = Action.objects.filter(action_type__in=("answer","comment")).filter(node__parent__author=request.user).order_by('-action_date') 
#    actions = Action.objects.filter(action_type__in=("answer","comment"))
    res = []
    for action in actions[:50]:
        item = {}
        item["Url"]=action.node.get_absolute_url()
        item["Type"]=_(action.action_type)
        item["FaviconUrl"]= settings.APP_URL + "/m/default/media/images/favicon.ico"
        item["SiteUrl"]= settings.APP_URL
        item["Count"]=0

        t = action.action_date
        time_z = "%s %s at %s:%s" % (t.month,t.day,t.hour,t.minute )
        item["CreationDate"]=time_z

        if action.node.added_at>request.user.last_login :
            item["IsNew"] = True
        else:
            item["IsNew"] = False
        if action.action_type == "answer":
            item["Title"]=action.node.parent.title
            item["Summary"]=action.node.summary[:20]+"..."
        elif action.action_type == "comment":
            node = action.node.parent
            if node.get_type() == "question":
                item["Title"]=action.node.parent.title
            else:
                item["Title"]=action.node.parent.summary[:20]
            item["Summary"]=action.node.summary[:20]+"..."

        res.append(item)
    return HttpResponse(simplejson.dumps(res), mimetype="application/json")

def question_list(request, initial,
                  list_description=_('questions'),
                  base_path=None,
                  page_title=_("All Questions"),
                  allowIgnoreTags=True,
                  feed_url=None,
                  paginator_context=None,
                  is_home_page=False,
                  tag = None,
                  known_tip = None):

    questions = initial.filter_state(deleted=False)

    if request.user.is_authenticated() and allowIgnoreTags:
        questions = questions.filter(~Q(tags__id__in = request.user.marked_tags.filter(user_selections__reason = 'bad')))

    if page_title is None:
        page_title = _("Questions")

    if request.GET.get('type', None) == 'rss':
        questions = questions.order_by('-added_at')
        return RssQuestionFeed(request, questions, page_title, list_description)(request)

    keywords =  ""
    if request.GET.get("q"):
        keywords = request.GET.get("q").strip()

    #answer_count = Answer.objects.filter_state(deleted=False).filter(parent__in=questions).count()
    #answer_description = _("answers")

    if not feed_url:
        req_params = "&".join(generate_uri(request.GET, (_('page'), _('pagesize'), _('sort'))))
        if req_params:
            req_params = '&' + req_params

        feed_url = mark_safe(escape(request.path + "?type=rss" + req_params))

    return pagination.paginated(request, ('questions', paginator_context or QuestionListPaginatorContext()), {
    "questions" : questions.distinct(),
    "questions_count" : len(questions),
    "keywords" : keywords,
    "list_description": list_description,
    "base_path" : base_path,
    "page_title" : page_title,
    "tab" : "questions",
    'feed_url': feed_url,
    'is_home_page' : is_home_page,
    'tag' : tag,
    'known_tip' : known_tip,
    })


def search(request):
    if request.method == "GET" and "q" in request.GET:
        keywords = request.GET.get("q")
        search_type = request.GET.get("t")

        if not keywords:
            return HttpResponseRedirect(reverse(index))
        if search_type == 'tag':
            return HttpResponseRedirect(reverse('tags') + '?q=%s' % urlquote(keywords.strip()))
        elif search_type == "user":
            return HttpResponseRedirect(reverse('users') + '?q=%s' % urlquote(keywords.strip()))
        else:
            return question_search(request, keywords)
    else:
        return render_to_response("search.html", context_instance=RequestContext(request))

@decorators.render('questions.html')
def question_search(request, keywords):
    #can_rank, initial = Question.objects.search(keywords)
    can_rank=False
    initial = Question.objects.filter(title__icontains=keywords) | Question.objects.filter(body__icontains=keywords)
    if can_rank:
        paginator_context = QuestionListPaginatorContext()
        paginator_context.sort_methods[_('ranking')] = pagination.SimpleSort(_('relevance'), '-ranking', _("most relevant questions"))
        paginator_context.force_sort = _('ranking')
    else:
        paginator_context = None

    feed_url = mark_safe(escape(request.path + "?type=rss&q=" + keywords))

    return question_list(request, initial,
                         #_("questions matching '%(keywords)s'") % {'keywords': keywords},
                         _("questions"),
                         None,
                         _("questions matching '%(keywords)s'") % {'keywords': keywords},
                         paginator_context=paginator_context,
                         feed_url=feed_url)


@decorators.render('tags.html', 'tags', _('tags'), weight=100)
def tags(request):
    stag = ""
    tags = Tag.active.all()

    if request.method == "GET":
        stag = request.GET.get("q", "").strip()
        if stag:
            tags = tags.filter(name__icontains=stag)

    return pagination.paginated(request, ('tags', TagPaginatorContext()), {
        "tags" : tags,
        "stag" : stag,
        "keywords" : stag
    })

def update_question_view_times(request, question):
    last_seen_in_question = request.session.get('last_seen_in_question', {})

    last_seen = last_seen_in_question.get(question.id, None)

    if (not last_seen) or (last_seen < question.last_activity_at):
        QuestionViewAction(question, request.user, ip=request.META['REMOTE_ADDR']).save()
        last_seen_in_question[question.id] = datetime.datetime.now()
        request.session['last_seen_in_question'] = last_seen_in_question

def match_question_slug(id, slug):
    slug_words = slug.split('-')
    qs = Question.objects.filter(title__istartswith=slug_words[0])

    for q in qs:
        if slug == urlquote(slugify(q.title)):
            return q

    return None

def answer_redirect(request, answer):
    pc = AnswerPaginatorContext()

    sort = pc.sort(request)

    if sort == _('oldest'):
        filter = Q(added_at__lt=answer.added_at)
    elif sort == _('newest'):
        filter = Q(added_at__gt=answer.added_at)
    elif sort == _('votes'):
        filter = Q(score__gt=answer.score) | Q(score=answer.score, added_at__lt=answer.added_at)
    else:
        raise Http404()

    count = answer.question.answers.filter(Q(marked=True) | filter).exclude(state_string="(deleted)").count()
    pagesize = pc.pagesize(request)

    page = count / pagesize
    
    if count % pagesize:
        page += 1
        
    if page == 0:
        page = 1

    return HttpResponsePermanentRedirect("%s?%s=%s#%s" % (
        answer.question.get_absolute_url(), _('page'), page, answer.id))

def tag_subscriber_info(request, name):
    tag = get_object_or_404(Tag, name=name)
    pt = MarkedTag.objects.filter(tag__name=tag).filter(subscribed=True)#todo,add   subscribed=True
    subscribed_count = len(pt)
    subscribed_tags = []
    if request.user.is_authenticated():
        subscribed_tags = pt.filter(user=request.user).values_list('tag__name', flat=True)

    return render_to_response('tag_subscriber_info.html', {
            'subscribed_tags':subscribed_tags,
            'subscribed_count' :subscribed_count,
            'tag': tag,
            }, context_instance=RequestContext(request))

def _diff_tag_post(revision,last_revision,use_default=False,render_mode=False):
    about_diff = None
    detail_diff = None
    descs = []

    if use_default:
        about_diff = revision.about
        detail_diff = revision.detail

    if last_revision is not None:
        if revision.about != last_revision.about:
            about_diff = mark_safe(htmldiff(revision.about,last_revision.about ))
            descs.append(_("edited about"))

        if revision.detail != last_revision.detail:
            if not render_mode:
                detail_diff = mark_safe(htmldiff(revision.detail,last_revision.detail )) 
            else:
                revision_detail = static_content(revision.detail,"markdown")
                last_revision_detail = static_content(last_revision.detail,"markdown")
                detail_diff = htmldiff(revision_detail,last_revision_detail,render_mode=True )
            descs.append(_("edited detail"))

    return (about_diff,detail_diff,",".join(descs))

def _diff_post(revision,last_revision,use_default=False,render_mode=False,is_answer=False):
    title_diff = None
    body_diff = None
    tags_diff = None
    descs = []

    if use_default:
        title_diff = revision.title
        body_diff = revision.html        
        tags_diff = mark_safe(tags_html(revision.tagname_list()))

    if last_revision is not None:
        if not is_answer and last_revision.title != revision.title:
            title_diff = mark_safe(htmldiff(revision.title,last_revision.title ))
            descs.append( _("edited title"))

        if revision.html != last_revision.html:
            if not render_mode:#markdown diff
                body_diff = mark_safe(htmldiff(revision.body,last_revision.body ))
            else:#render html diff
                revision_html = static_content(revision.html,"markdown")
                last_revision_html = static_content(last_revision.html,"markdown")
                body_diff = htmldiff(revision_html,last_revision_html,render_mode=True )
            descs.append(_("edited body"))

        current_tags = " ".join(revision.tagname_list())
        last_tags = " ".join(last_revision.tagname_list())
        if last_tags != current_tags:
            tags_diff = tagsdiff(current_tags,last_tags)
            tags_diff = mark_safe(tags_html(tags_diff))
            descs.append(_("edited tags"))
            
    return (title_diff,body_diff,tags_diff,",".join(descs))
    

def post_body(request,id):
    action = get_object_or_404(Action, id=id)
    post = get_object_or_404(Node, id=action.node.id).leaf

    if action.action_type in [ "revise" , "suggest" ]:
        revisions = list(post.revisions.order_by('revised_at'))
        revision = None
        last_revision = None

        for  i, revise in enumerate(revisions):
            if revise.revised_at.ctime() == action.at.ctime():
                revision = revise
                break
            else:
                last_revision = revise
    
        (title_diff,body_diff,tags_diff,desc) = _diff_post(revision,last_revision,is_answer=(type(post)==Answer))
            
        return render_to_response('node/revision.html', {
                'title': title_diff,
                'html': body_diff,
                'tags': tags_diff,
                }, context_instance=RequestContext(request))        

    return render_to_response('node/post.html', {
    'post': post,
    'action':action
    }, context_instance=RequestContext(request))

def user_flair_html(request,id):
    user = get_object_or_404(User, id=id)
    return render_to_response('user_flair.html',{
            'user':user,
            },context_instance=RequestContext(request))

def user_flair(request,name,id):
    user = get_object_or_404(User, id=id)
    return render_to_response('flair.html',{
            'user':user,
            "can_view_private": (user == request.user) or request.user.is_superuser,
            'view_user':user,
            },context_instance=RequestContext(request))

def user_info(request, id):
    user = get_object_or_404(User, id=id)
    return render_to_response('user_info.html', {
    'user': user,
    }, context_instance=RequestContext(request))

def user_day_rep(request,id,year,month,day):
    user = get_object_or_404(User, id=id)

    reps = user.reputes.filter(Q(date__year=year)&Q(date__month=month)&Q(date__day=day)).order_by('-date')
    return render_to_response('users/user_day_rep.html', {
    'reps': reps,
    }, context_instance=RequestContext(request))

def tag_info(request, id):
    tag = get_object_or_404(Tag, id=id)
    editors = len(tag.revisions.values('author_id').distinct())
    hot_questions = Question.objects.filter(tags__id=tag.id)[:10]
    top_answerers_ids = Answer.objects.filter(parent__tags__id=tag.id).values('author').annotate(Count('author')).order_by('-author__count')[:5]
    top_answerers = []
    for a in top_answerers_ids:
        top_answerers.append(User.objects.get(id=a["author"]))

    #update tag view times
    last_seen_in_tag = request.session.get('last_seen_in_tag', {})
    last_seen = last_seen_in_tag.get(tag.id, None)

    if (not last_seen) :
        TagViewAction(tag, ip=request.META['REMOTE_ADDR']).save()
        last_seen_in_tag[tag.id] = datetime.datetime.now()
        request.session['last_seen_in_tag'] = last_seen_in_tag

    return render_to_response('tag_info.html', {
    'tag': tag,
    'editors':editors,
    'hot_questions':hot_questions,
    'top_answerers':top_answerers,
    }, context_instance=RequestContext(request))

@decorators.render("question.html", 'questions')
def question(request, id, slug='', answer=None):
    try:
        question = Question.objects.get(id=id)

        question_headline = question.headline
        question_body = question.html
        tags = question.tags.all()

        if question.pendding_suggestion and question.pendding_suggestion.author == request.user:
            question_body = static_content(question.pendding_suggestion.body,"markdown")
            question_headline = question.pendding_suggestion.title
            tags = list(Tag.objects.filter(name__in=question.pendding_suggestion.tagname_list()))

    except:
        if slug:
            question = match_question_slug(id, slug)
            if question is not None:
                return HttpResponseRedirect(question.get_absolute_url())

        raise Http404()

    if question.nis.deleted and not request.user.can_view_deleted_post(question):
        raise Http404

    if request.GET.get('type', None) == 'rss':
        return RssAnswerFeed(request, question, include_comments=request.GET.get('comments', None) == 'yes')(request)

    if answer:
        answer = get_object_or_404(Answer, id=answer)

        if (question.nis.deleted and not request.user.can_view_deleted_post(question)) or answer.question != question:
            raise Http404

        if answer.marked:
            return HttpResponsePermanentRedirect(question.get_absolute_url())

        return answer_redirect(request, answer)

    if settings.FORCE_SINGLE_URL and (slug != slugify(question.title)):
        return HttpResponsePermanentRedirect(question.get_absolute_url())

    if request.POST:
        answer_form = AnswerForm(request.POST, user=request.user)
    else:
        answer_form = AnswerForm(user=request.user)

    answers = request.user.get_visible_answers(question)

    update_question_view_times(request, question)

    if request.user.is_authenticated():
        try:
            subscription = QuestionSubscription.objects.get(question=question, user=request.user)
        except:
            subscription = False
    else:
        subscription = False

    return pagination.paginated(request, ('answers', AnswerPaginatorContext()), {
    "question" : question,
    "question_headline" : question_headline,    
    "question_body" : question_body,
    "tags" : tags,
    "answer" : answer_form,
    "answers" : answers,
    "similar_questions" : question.get_related_questions(),
    "subscription": subscription,
    })

@decorators.render("privileges.html", 'privileges')
def privileges(request,slug=''):
    privilege_list = []
    slug = slug.replace("-"," ")
    select_priv = None

    if request.user.is_authenticated():
        current_value = request.user.reputation
    else:
        current_value = 0

    for priv in  PRIVILEGE_SET:
        if priv is ALL_PRIVILEGE_PAGE:
            continue
        p = {}
        p["name"] = priv.field_context["label"]
        p["href"] = p["name"].replace(" ","-")
        p["value"] = priv.field_context["reputation"].value
        proc = 100
        if current_value < p["value"]:
            proc = ((current_value+0.0)*100//p["value"])
        p["proc"] = proc
        p["here"] = False
        if slug == p["name"]:
            p["here"] = True
            select_priv = priv
        privilege_list.append(p)

    privilege_list = sorted(privilege_list,key = lambda priv:priv["value"],reverse=True)

    title = ""
    desc = ""
    if select_priv:
        title = select_priv.field_context["label"]
        current_value = select_priv.field_context["reputation"].value
        desc = select_priv.value
    else:
        title = ALL_PRIVILEGE_PAGE.field_context["label"]
        desc = ALL_PRIVILEGE_PAGE.value

    return render_to_response('privileges.html', {
            "privileges":privilege_list,
            "select_priv":select_priv,
            "current_value":current_value,
            "title":title,
            "desc":desc,
            }, context_instance=RequestContext(request));

REVISION_TEMPLATE = template.loader.get_template('node/revision.html')

def tag_revisions(request,id):
    post = get_object_or_404(Tag, id=id)

    revisions = list(post.revisions.exclude(suggest_status="pendding").order_by('revised_at'))

    rev_ctx = []

    last_revision = None
    about_diff,body_diff = (None,None)
    edit_desc = None
    for i, revision in enumerate(revisions):
        if i > 0 :
            (about_diff,body_diff,edit_desc) = _diff_tag_post(revision,last_revision,use_default=True)
        else:
            (about_diff,body_diff) = (revision.about,revision.detail)

        rev_ctx.append(dict(inst=revision))
        rev_ctx[i]['title'] = about_diff
        rev_ctx[i]['html'] = body_diff

        if len(revision.summary) == 0:
            rev_ctx[i]['summary'] = edit_desc
        else:
            rev_ctx[i]['summary'] = revision.summary

        last_revision = revision

    rev_ctx.reverse()

    return render_to_response('revisions.html', {
    'post': post,
    'revisions': rev_ctx,
    }, context_instance=RequestContext(request))

def revisions(request, id ):
    post = get_object_or_404(Node, id=id).leaf

    revisions = list(post.revisions.exclude(suggest_status="pendding").order_by('revised_at'))
    rev_ctx = []

    last_revision = None
    title_diff,body_diff,tags_diff = (None,None,None)
    edit_desc = None
    for i, revision in enumerate(revisions):
        if i > 0 :
            (title_diff,body_diff,tags_diff,edit_desc) = _diff_post(revision,last_revision,use_default=True)
        else:
            (title_diff,body_diff,tags_diff) = (revision.title,revision.html,mark_safe(tags_html(revision.tagname_list())))

        rev_ctx.append(dict(inst=revision))
        rev_ctx[i]['title'] = title_diff
        rev_ctx[i]['html'] = body_diff
        rev_ctx[i]['tags'] = tags_diff        

        if len(revision.summary) == 0:
            rev_ctx[i]['summary'] = edit_desc
        else:
            rev_ctx[i]['summary'] = revision.summary

        last_revision = revision

    rev_ctx.reverse()

    return render_to_response('revisions.html', {
            'post': post,
            'revisions': rev_ctx,
            'is_post':True,
            }, context_instance=RequestContext(request))

def suggested_edits_tag(request,id):
    tag = get_object_or_404(Tag,id=id)
    suggestion = tag.pendding_suggestion    

    if suggestion is None:
        return HttpResponse(_("suggestion has been handled by others!"), status=404,content_type="text/plain")
    
    (about_diff,render_detail_diff,edit_desc) = _diff_tag_post(suggestion,tag.active_revision,use_default=True,render_mode=True)
    (t,markdown_detail_diff,t) = _diff_tag_post(suggestion,tag.active_revision,use_default=True)

    detail_text_body = tag.active_revision.detail.replace("\n", "<br>").replace(" ","&nbsp;")

    if len(suggestion.summary) == 0:
        summary = edit_desc
    else:
        summary = suggestion.summary

    post_type = type(tag).__name__.lower()

    return render_to_response('suggest_check.html', {
            'post': tag,
            'title_diff':about_diff,
            'render_body_diff':render_detail_diff,
            'post_text_body':detail_text_body,
            'markdown_body_diff':markdown_detail_diff,
            'summary':summary,
            'post_type':post_type,
            }, context_instance=RequestContext(request))


def suggested_edits(request,id,isTag=False):
    post = get_object_or_404(Node, id=id).leaf
    suggestion = post.pendding_suggestion

    if suggestion is None:
        return HttpResponse(_("suggestion has been handled by others!"), status=404,content_type="text/plain")
 
    (title_diff,render_body_diff,tags_diff,edit_desc) = _diff_post(suggestion,post.active_revision,use_default=True,render_mode=True)

    (t,markdown_body_diff,t,t) = _diff_post(suggestion,post.active_revision,use_default=True)
    post_text_body = post.active_revision.body.replace("\n", "<br>").replace(" ","&nbsp;")

    if len(suggestion.summary) == 0:
        summary = edit_desc
    else:
        summary = suggestion.summary

    post_type = type(post).__name__.lower()

    return render_to_response('suggest_check.html', {
            'post':post,
            'title_diff':title_diff,
            'render_body_diff':render_body_diff,
            'post_text_body':post_text_body,
            'markdown_body_diff':markdown_body_diff,
            'tags_diff':tags_diff,
            'summary':summary,
            'post_type':post_type,
            }, context_instance=RequestContext(request))

