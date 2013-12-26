from base import Setting, SettingSet
from django.forms.widgets import Textarea
from minrep import *

PRIVILEGE_SET = SettingSet('privilege', 'Privilege page', "Define the text in the Privilege page. You can use markdown and some basic html tags.", 5000, True)

ALL_PRIVILEGE_PAGE = Setting('ALL_PRIVILEGE_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "all privileges",
help_text = """
ALL_PRIVILEGE_PAGE
""",
widget=Textarea(attrs={'rows': '20'})))

CREATE_POSTS_PAGE = Setting('CREATE_POSTS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "create post",
reputation = REP_TO_CREATE_POSTS,
help_text = """
CREATE_POSTS_PAGE
""",
widget=Textarea(attrs={'rows': '20'})))

CREATE_WIKI_POSTS_PAGE = Setting('CREATE_COMMUNITY_WIKI_POSTS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "create wiki posts",
reputation = REP_TO_WIKIFY,
help_text = """
create wiki posts
""",
widget=Textarea(attrs={'rows': '20'}))) 


VOTE_UP_PAGE = Setting('VOTE_UP_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "vote up",
reputation = REP_TO_VOTE_UP,
help_text = """
vote up
""",
widget=Textarea(attrs={'rows': '20'}))) 

VOTE_DOWN_PAGE = Setting('VOTE_DOWN_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "vote down",
reputation = REP_TO_VOTE_DOWN,
help_text = """
vote down
""",
widget=Textarea(attrs={'rows': '20'}))) 

FLAG_POSTS_PAGE = Setting('FLAG_POSTS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "flag posts",
reputation = REP_TO_FLAG,
help_text = """
flag post
""",
widget=Textarea(attrs={'rows': '20'}))) 

RETAG_QUESTIONS_PAGE = Setting('RETAG_QUESTIONS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "retag questions",
reputation = REP_TO_RETAG,
help_text = """
retag questions
""",
widget=Textarea(attrs={'rows': '20'}))) 

CREATE_TAGS_PAGE = Setting('CREATE_TAGS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "create tags",
reputation = REP_TO_CREATE_TAGS ,
help_text = """
create tags
""",
widget=Textarea(attrs={'rows': '20'}))) 

EDIT_QUESTIONS_AND_ANSWERS_PAGE = Setting('EDIT_QUESTIONS_AND_ANSWERS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "edit questions and answers",
reputation = REP_TO_EDIT_OTHERS ,
help_text = """
edit questions and answers
""",
widget=Textarea(attrs={'rows': '20'}))) 

APPROVE_TAG_WIKI_EDITS_PAGE = Setting('APPROVE_TAG_WIKI_EDITS_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "approve tag wiki edits",
reputation = REP_TO_EDIT_OTHERS ,
help_text = """
approve tag wiki edits
""",
widget=Textarea(attrs={'rows': '20'}))) 

EDIT_COMMUNITY_WIKI_PAGE = Setting('EDIT_COMMUNITY_WIKI_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "edit community wiki",
reputation = REP_TO_EDIT_WIKI ,
help_text = """
edit community wiki
""",
widget=Textarea(attrs={'rows': '20'}))) 

COMMENT_EVERYWHERE_PAGE = Setting('COMMENT_EVERYWHERE_PAGE',
u"""
**Please customize this text in the administration area**
""", PRIVILEGE_SET, dict(
label = "comment everywhere",
reputation = REP_TO_COMMENT ,
help_text = """
comment everywhere
""",
widget=Textarea(attrs={'rows': '20'}))) 
