#!/usr/bin/env python3
# coding: utf-8

from functools import reduce
import os
import re
import time

from bs4 import BeautifulSoup

from lib.logger import LOG
from lib.logger import LOG_TIME
from lib.logger import LOG_TIME_END
from . import H

# Filter special unicode
def filter_non_CJK_unicode(char):
    _char = char.group(0)
    # Ref: https://zh.wikipedia.org/wiki/Unicode#.E6.BC.A2.E5.AD.97.E5.95.8F.E9.A1.8C
    # Ref: https://gist.github.com/shingchi/64c04e0dd2cbbfbc1350
    # Ref: http://www.programmer-club.com.tw/ShowSameTitleN/general/4309.html
    CONDITION = [
        int("3001", 16)
        <= ord(_char)
        <= int("303F", 16),  # CJK 標點符號; Note: 0x3000 is a empty space
        int("0020", 16) <= ord(_char) <= int("007E", 16),  # 0-9a-zA-Z & 半形符號
        int("4E00", 16) <= ord(_char) <= int("FFEF", 16),  # Unicode CJK 常用字
        int("000A", 16) <= ord(_char) <= int("000A", 16),  # 換行符號
        int("2026", 16) <= ord(_char) <= int("2026", 16),  # "…" 沈默符號
    ]
    if reduce(lambda prev, curr: prev or curr, CONDITION):
        return _char
    else:
        return ""


def main_handle(buf, treat_as_pure_text, skip_trim=False):
    def handle(buf):
        LOG("MODE: %s" % treat_as_pure_text)
        if skip_trim:
            return buf
        buf = re.sub("<script.*?</script>", "", buf, flags=re.DOTALL)
        buf = re.sub("<style.*?</style>", "", buf, flags=re.DOTALL)
        buf = re.sub("<template.*?</template>", "", buf, flags=re.DOTALL)
        buf = re.sub("<fon.*?>.*?</font>", "", buf, flags=re.DOTALL)
        buf = re.sub("<!--.*?-->", "", buf, flags=re.DOTALL)

        if treat_as_pure_text == "1":
            buf = re.sub(
                r"<(.{0,1000}?)(?: |.){0,1000}?>(.{0,1000}?)</\1>",
                r"",
                buf,
                flags=re.DOTALL | re.DEBUG | re.VERBOSE,
            )
        elif treat_as_pure_text == "2":
            buf = re.sub(
                r"<(.{0,1000}?)(?: |.){0,1000}?>(.{0,1000}?)</\1>",
                r"\2",
                buf,
                flags=re.DOTALL | re.DEBUG | re.VERBOSE,
            )
        elif treat_as_pure_text == "3":
            buf = re.sub(
                r"<(.{0,1000}?)(?: |.){0,1000}?>(.{0,1000}?)</\1>",
                r"",
                buf,
                flags=re.DEBUG | re.VERBOSE,
            )
        elif treat_as_pure_text == "4":
            buf = re.sub(
                r"<(.{0,1000}?)(?: |.){0,1000}?>(.{0,1000}?)</\1>",
                r"\2",
                buf,
                flags=re.DEBUG | re.VERBOSE,
            )
        elif treat_as_pure_text == "5":
            soup = BeautifulSoup(buf, "html.parser")  # default
            buf = soup.getText()
        elif treat_as_pure_text == "6":
            soup = BeautifulSoup(buf, "html5lib")
            buf = soup.getText()
        elif treat_as_pure_text == "7":
            soup = BeautifulSoup(buf, "lxml")
            buf = soup.getText()
        buf = H.unescape(buf)
        return buf

    # Handle continuously until no any removable character exists inside buf
    prev = ""
    curr = buf
    while prev != curr:
        LOG("prev: %s" % len(prev))
        prev = curr
        curr = handle(curr)
        LOG("curr: %s" % len(curr))
    buf = curr

    if not skip_trim:
        # remove weird space symbol
        buf = re.sub(r"(?:\xc2|\xa0)+", " ", buf, flags=re.DOTALL)
        buf = re.sub(r"^ +", "", buf, flags=re.MULTILINE)
        buf = re.sub(r"^ +", "", buf, flags=re.MULTILINE)
        buf = re.sub(r" +$", "", buf, flags=re.MULTILINE)
        # https://www.scivision.dev/hex-code-c2a0-non-breaking-space-markdown/
        buf = re.sub(r"(?:\t)+", "", buf, flags=re.MULTILINE)

        # remove duplicated tail symbol
        buf = re.sub(r"((?:﹖|﹗|。|？|！|…))(?=\1)", "", buf, flags=re.DOTALL)

        # add extra line wrap
        buf = re.sub(r"((?:｢|「))", "\n\g<1>", buf, flags=re.DOTALL)
        buf = re.sub(r"((?:｣|」))", "\g<1>\n", buf, flags=re.DOTALL)
        buf = re.sub(r"((?:。){1}(?!｣|」))", "\g<1>\n", buf, flags=re.DOTALL)

        buf = re.sub(r"((?:｣|｢){1})", "\g<1>\n", buf, flags=re.MULTILINE)

        # remove duplicated line wrap symbol
        buf = re.sub(r"((?:\n))+", "\g<1>", buf, flags=re.DOTALL)
    return buf


def post_handle(buf, chapterType, ocrMode, autoPagination):
    def chapter_handler(char):
        try:
            chapterNo = char.group("chapterNo")
            chapterName = char.group("chapterName")
        except Exception as e:
            return char.group(0)
        return f"\n\n第{chapterNo}章 {chapterName}\n\n"

    if chapterType == "number":
        buf = re.sub(
            r"^(?P<chapterNum>\d+)\n",
            r"\n\n第\g<chapterNum>章\n\n",
            buf,
            flags=re.MULTILINE,
        )
    elif chapterType == "、":
        pattern = r"^(?P<chapterNo>\d+)、(?P<chapterName>.*)\n"
        buf = re.sub(pattern, chapter_handler, buf, flags=re.MULTILINE)
    else:
        pattern = r"^(?P<chapterNo>\d+) (?P<chapterName>.*)\n"
        buf = re.sub(pattern, chapter_handler, buf, flags=re.MULTILINE)

    # NOTE: add final wrap and avoid duplicated wrap at the end of content
    output = re.sub(r"((?:\r*\n))+$", "\n", buf, flags=re.MULTILINE)

    if ocrMode == "1":
        output = re.sub(
            r"^第(?P<chapterNum>(?: ){0,}\d+(?: ){0,})(?:章|話)\n",
            r"@@@@第\g<chapterNum>章@@@@",
            buf,
            flags=re.MULTILINE,
        )
        prev = ""
        curr = output
        while prev != curr:
            prev = curr
            curr = re.sub(r"\n", "", curr)
        output = curr
        output = re.sub(
            r"@@@@第(?P<chapterNum>\d+)章@@@@",
            r"\n\n第\g<chapterNum>章\n\n",
            output,
            flags=re.MULTILINE,
        )
        output = re.sub(
            r"(?P<wrapWord1>)(?: )+(?P<wrapWord2>)",
            r"\g<wrapWord1>\g<wrapWord2>",
            output,
            flags=re.MULTILINE,
        )
        output = re.sub(
            r"(?P<wrapWord>。)",
            r"\g<wrapWord>\n",
            output,
            flags=re.MULTILINE,
        )
    if autoPagination != "0":
        paginationPosList = []
        paginationSize = int(autoPagination)
        maxPos = len(output) - 1
        currPos = paginationSize
        while currPos < maxPos:
            fragment = output[currPos : currPos + paginationSize]
            paginationPosList.append(currPos + fragment.find("\n") + 1)
            currPos += paginationSize
        paginationPosList.append(currPos)
        newOutput = ""
        for idx, pos in enumerate(paginationPosList):
            start = 0 if idx == 0 else paginationPosList[idx - 1]
            end = pos
            newOutput = newOutput + f"\n第{idx + 1}話\n\n" + output[start:end]
        return newOutput
    return output


def content_handle(
    buf,
    treat_as_pure_text=os.environ.get("TXTMODE", "5").upper(),
    chapterType="text",
    ocrMode="0",
    autoPagination="0",
    skip_trim=False,
):
    LOG_TIME('filter_non_CJK_unicode prepare')
    # https://docs.python.org/3/library/re.html#re.DOTALL
    buf = re.sub(r"(?:.)", filter_non_CJK_unicode, buf, flags=re.DOTALL)
    LOG_TIME_END('filter_non_CJK_unicode prepare')
    buf = main_handle(buf, treat_as_pure_text, skip_trim)
    LOG_TIME('main_handle done')
    buf = post_handle(buf, chapterType, ocrMode, autoPagination)
    LOG_TIME_END('main_handle done')

    return buf
