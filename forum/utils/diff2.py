import diff_match_patch as dmp_module
import re
from htmltreediff import diff as render_tree_diff
from htmldiff import render_html_diff

#\<(?P<html_tag>[\w]+) (?P<attr>[\w-]+)\>(?P<text>[.]+)\<\/P<html_tag_end>[\w]+)\>

pattern = re.compile("""
<(?P<html_tag>[\w]+) (?P<attr>.*)\>(?P<text>.*)<\/(?P<html_tag_end>[\w]+)>
"""
,re.I|re.X)


def textDiff(new,old,render_mode=False):
    if new is None :
        return ""
    if old is None :
        return new

    if render_mode :
        new = new.replace("\n",";nwsp;")
        old = old.replace("\n",";nwsp;")
        #text = render_html_diff(old,new)
        text = render_tree_diff(old,new)
        text = text.replace(";nwsp;","\n")
    else:
        new = new.replace(" ","&nbsp;")
        old = old.replace(" ","&nbsp;")
        dmp = dmp_module.diff_match_patch()
        diffs = dmp.diff_main(old,new)
        text = dmp.diff_prettyHtml(diffs,render_mode=render_mode)

    return text

def _is_new_tag(tag):
    if len(tag) == 0:
        return False
    if tag[-1:] == " " or tag[-7:] == " </ins>" or tag[-7:] == " </del>":
        return True
    return False


def _inline_split(tags_list):
    tags_list_1 = []
    for tag in tags_list:
        if "</del>" not in tag and "</ins>" not in tag:
            tags = tag.split()
            for tag in tags:
                tags_list_1.append( tag + " " )
        else:
            ret = pattern.match(tag)
            if ret is not None:
                html_tag = ret.group("html_tag")
                html_attr = ret.group("attr")
                tag_text =  ret.group("text")
                tags = tag_text.split()
                if len(tags) == 0:
                    tags=["&nbsp"];#tags_list_1.append(tag)
                tag_template = '<%(html_tag)s %(attr)s>%(tag)s</%(html_tag)s>'
                for tag in tags:
                    tags_list_1.append(
                        tag_template % {
                            "html_tag" : html_tag,
                            "attr" : html_attr,
                            "tag" : tag+" "
                            }
                        )
            else:
                tags_list_1.append(tag)
    return tags_list_1
    

def tagsDiff(new,old):
    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(old,new)
    tags_list = dmp.diff_prettyHtml(diffs,tag_mode=True)

    tags_list = _inline_split(tags_list)

    tags_list_new = []
    last_tag = tags_list[0]
    tags_list = tags_list[1:]
    for tag in tags_list:
        if not _is_new_tag(last_tag) :
            tags_list_new.append(last_tag+tag)
            last_tag=""
        else:
            tags_list_new.append(last_tag)
            last_tag = tag
    if last_tag:
        tags_list_new.append(last_tag)
    return tags_list_new
