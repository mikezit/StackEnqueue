from base import Setting, SettingSet
from django.forms.widgets import Textarea

PAGES_SET = SettingSet('known_tips', 'known tips page', "Define the text in the known tips page. You can use markdown and some basic html tags.", 2000, True)

KNOWN_TIPS_PAGE_TEXT = Setting('KNOWN_TIPS_PAGE_TEXT',
u"""
[tips1]
[tips2]
[tips3]
""", PAGES_SET, dict(
label = "Known tips page text",
help_text = """
The known tips page.
""",
widget=Textarea(attrs={'rows': '20'})))
