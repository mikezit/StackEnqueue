#!/usr/bin/env python
# coding=utf-8

import os.path
from pinyin_data import pinyin_code 

VERSION = '0.1'

def get_pinyin(chars, splitter=''):
    result = []
    for char in chars:
        key = "%X" % ord(char)
        try:
            result.append(pinyin_code[key].split(" ")[0].strip()[:-1]\
                              .lower())
        except:
            result.append(char)

    return splitter.join(result)

def get_initials(char):
    try:
        return pinyin_code["%X" % ord(char)].split(" ")[0][0]
    except:
        return char

def test():
    print get_pinyin(u'我爱你12dd%$^&*3sdaf')

def main():
    test()

if __name__ == "__main__":
    main()
