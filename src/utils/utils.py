import logging
import asyncio
import aiohttp
import os, time, json, gc

from dotenv import load_dotenv

import logging

load_dotenv()
logLevel = os.getenv("LOG_LEVEL", default="DEBUG")

# logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)




def set_log_level(logger, level: str):
    if level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif level == "INFO":
        logger.setLevel(logging.INFO)
    elif level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.DEBUG)


def extractURLs(ret):
    """ Extract URLs from the search results."""
    urls = []
    for val in ret:
        urls.append(val["link"])
    return urls


def joinContext(ret, separator=None):
    """
    Combine content
    """
    string=""
    for val in ret:
        # print(val)
        if separator :
            string += (val) + separator
        else :
            string += (val) + " "
    return string 


def extractMarkdown(ret, types="all", extract="raw_markdown"):
    markdowns= []
    if types == "all":
        for item in ret:
            # data = item["_results"][0] # extract # new version
            logger.info(f"Extracting markdown from item: {type(item)}")
            data = item # old version
            print(f"Markdown: {data.markdown.raw_markdown[:200]}...")  
            markdowns.append(data.markdown.raw_markdown)

    elif types == "markdown":
        for item in ret:
            markdowns.append(item["markdown"])
    return markdowns