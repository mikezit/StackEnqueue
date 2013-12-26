import markdown
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags
from forum.utils.html import sanitize_html
from markdown.util import isBlockLevel

PRE_CLASS = "prettyprint"

class PreTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        blocks = root.getiterator('pre')
        for block in blocks:
            if isBlockLevel(block.tag):
                cls = block.get('class')
                if cls:
                    block.set('class', '%s %s' % (cls, PRE_CLASS))
                else:
                    block.set('class', PRE_CLASS)
        
        return root

class CodeShowExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.treeprocessors.add("code_show", PreTreeprocessor(md), ">inline")

def makeExtension(configs=None) :
    return CodeShowExtension(configs=configs)
