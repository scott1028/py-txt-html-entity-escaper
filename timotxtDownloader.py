#!/usr/bin/env python3
# coding: utf-8

import re

from lib.NovelGrabber import NovelGrabber


class CzNovelGrabber(NovelGrabber):
    def get_title_reg(self):
        reg_title = re.compile(r'<a.*?href=".*?".*?aria-current="page".*?>(?P<title>.*?)</a>', re.DOTALL)
        return reg_title

    def get_article_area_reg(self):
        reg_article = re.compile(
            '<div.*?class="header.*?has-btn">.*?(?P<article>.*?)</ul><div.*?class="gadBlock"', re.DOTALL
        )
        return reg_article

    def get_chapter_urls_reg(self):
        reg_url = re.compile(
            '<li><a.*?href.*?="(?P<url>.*?)".*?>.*?</li>', re.MULTILINE
        )
        return reg_url

    def get_base_novel_link_url_prefix(self, url=None):
        novel_link_url_prefix = "https://www.timotxt.com"
        return novel_link_url_prefix

    def get_novel_content_reg(self):
        # <div class="chapter-content
        reg_content = re.compile(
            '<div.*?class.*?=.*?"chapter-content".*?>(?P<content>.*?)<ad.*?pos="bottom">',
            re.DOTALL,
        )
        return reg_content


if __name__ == "__main__":
    CzNovelGrabber(TXTENCODE="utf-8", tip="ex: https://www.timotxt.com/2105128652/dir").run()
