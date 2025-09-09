"""
# SearxNG Web Search Engine

You can [check this link](https://docs.searxng.org/dev/search_api.html) for more informations about `Searx API` parameters.
#### Download SearxNG docker for local host setup web search Engine

"""


import pprint
from langchain_community.utilities import SearxSearchWrapper
import os , json, time , gc
import logging

from utils.utils import set_log_level

searchGeneralConfig = "!general"
searchImageConfig = "!images !bii !brimg !ddi !goi"
searchVideoConfig = "!videos !biv !brvid !ddv !gov"
searchNewConfig = "!news !gon !yhn"
searchMapConfig = "!map paris"
searchYouTubeConfig = "!yt"
searchSocialMedia = "!social_media !re !toot !mah !leco"
searchOptimalConfig = ":en :en-US :zh :zh-HK !go !bi !br !yh !goo !nvr !ddg !wd !wp"
defaultQueryTime = ""  # "month" #"year"


searxHost = "http://localhost:8080"  # for langchain
searxHost2 = "http://localhost:8080/search"  # for Searxng API directly


# inital Searxng search wrapper
search = SearxSearchWrapper(searx_host=searxHost, k=5)

logLevel = os.getenv("LOG_LEVEL", default="DEBUG")

# logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


set_log_level(logger, logLevel)



## Find URL web page for the query use langchain Searxng search wrapper
def searchURL(q, k=3, qureyTime=defaultQueryTime, 
              engines=["duckduckgo", "qwant", "google", "brave"],
              categories="general",
              querySuffix=searchOptimalConfig):
    results = search.results(q, 
                        num_results=k,
                        time_range=qureyTime,
                        engines=engines,
                        categories=categories,
                        query_suffix=querySuffix)

    return results

async def asyncSearchURL(q, k=3, qureyTime=defaultQueryTime,
                         engines=["duckduckgo", "qwant", "google", "brave"],
                         categories="general",
                         querySuffix=searchOptimalConfig):
    startTime = time.time()
    results = await search.aresults(q, 
                        num_results=k,
                        time_range=qureyTime,
                        engines= engines,
                        categories = categories,
                        query_suffix = querySuffix,)
    print(f"Time take: {time.time() - startTime}")
    print(f"Query Categores : {categories}")
    return results






