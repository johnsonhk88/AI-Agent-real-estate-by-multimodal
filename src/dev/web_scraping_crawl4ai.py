"""
Web Scraping using Crawl4AI version: 0.7.4+
New features:
- support deep crawling

"""
import pandas as pd
import matplotlib.pyplot as plt
import os , json, time , gc
import logging
import base64
import psutil

import asyncio
import aiohttp
# import html5lib
# import scrapy

from dotenv import load_dotenv
from IPython.display import HTML, Markdown, Image, Video
from tqdm import tqdm
from openai import OpenAI, AsyncOpenAI


from utils.utils import set_log_level
import os , json, time , gc
import logging



from crawl4ai import  AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, AdaptiveCrawler
import crawl4ai
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy, BestFirstCrawlingStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter,
    ContentRelevanceFilter,
    SEOFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer


from crawl4ai.chunking_strategy import (RegexChunking, 
                                        NlpSentenceChunking,
                                        OverlappingWindowChunking, 
                                        SlidingWindowChunking,
                                        FixedLengthWordChunking, 
                                        TopicSegmentationChunking) 

from crawl4ai.extraction_strategy import ( JsonCssExtractionStrategy, 
                                           JsonXPathExtractionStrategy,
                                          LLMExtractionStrategy, 
                                          CosineStrategy)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter, LLMContentFilter

from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
from crawl4ai import CrawlerMonitor, DisplayMode

from crawl4ai import AdaptiveConfig

load_dotenv()

os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"


# define browser configuration
browser_config1= BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    # for better performance in Docker or low memory menivroment 
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
    )


# support output pdf and screenshot
crawler_config1 = CrawlerRunConfig(
            page_timeout=60000, #30000, # for each image 
            wait_for_images=True,
            verbose=True,)

crawler_config2 = CrawlerRunConfig(
            word_count_threshold=10, 
            excluded_tags=["form", "header"],
            exclude_external_links=True,
    
            markdown_generator=DefaultMarkdownGenerator(),
            # Content processing
            process_iframes=True,
            remove_overlay_elements=True,

            # Cache control 
            # cache_mode=CacheMode.ENABLED,
            cache_mode=CacheMode.BYPASS, # fetch each time
    
            page_timeout=15000,  #60000, #30000, # for each image 
            wait_for_images=True,
            verbose=True,)

crawler_config3 = CrawlerRunConfig(
            word_count_threshold=10, 
            excluded_tags=["nav", "form", "header"],
            exclude_external_links=True,
    
            markdown_generator=DefaultMarkdownGenerator(
                options=  {"ignore_links": False,
                        "escape_html": False,
            # "body_width": 80
                          }
            ),
            # Content processing
            process_iframes=True,
            remove_overlay_elements=True,
            
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=2, 
                include_external=False,
                max_pages=20,              # Maximum number of pages to crawl (optional)
                # score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
                
                
            ),
            # scraping_strategy=LXMLWebScrapingStrategy(),
            # Cache control 
            # cache_mode=CacheMode.ENABLED,
            cache_mode=CacheMode.BYPASS, # fetch each time
    
            page_timeout=15000, #60000, #30000, # for each image 
            wait_for_images=True,
            verbose=True,
            pdf = False,
            screenshot = False,
            stream=False
        )


# Support Deep Crawling or adaptive Crawling Config generation functions

def generateBFSConfig(max_depth=2, include_external= False, max_pages=20, allow_domains=None):
    if allow_domains is not None:
        filter_chain = FilterChain([
            ContentTypeFilter(allowed_types=["text/html"]),
            DomainFilter(allowed_domains=allow_domains)

        ])
    else:
        filter_chain = FilterChain([
            ContentTypeFilter(allowed_types=["text/html"])
        ])
    
    return CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=max_depth, 
            include_external=include_external,
            max_pages=max_pages,
            filter_chain= filter_chain
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS, # fetch each time
        verbose=True,
        stream=False)
    
def generateDFSConfig(max_depth=2, include_external=False, max_pages=20):
        filter_chain  = FilterChain([
        ContentTypeFilter(allowed_types=["text/html"])
    
        ])
        return CrawlerRunConfig(
            DFSDeepCrawlStrategy(
                max_depth=max_depth, 
                include_external=include_external,
                max_pages=max_pages,
                filter_chain=filter_chain
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            cache_mode=CacheMode.BYPASS, # fetch each time
            verbose=True,
            stream=False)

def generateBestFirstConfig(max_depth=2, include_external=False, max_pages=15, keywords= [], weight=0.7):
    scorer = KeywordRelevanceScorer(
                keywords=keywords,
                weight=weight
        )
    filter_chain  = FilterChain([
        ContentTypeFilter(allowed_types=["text/html"])
    
    ])
    return CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=max_depth,
            include_external=include_external,
            url_scorer=scorer,
            max_pages=max_pages,              # Maximum number of pages to crawl (optional)
            filter_chain=filter_chain
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS, # fetch each time
        verbose=True,
        stream=False  
    )


def generateBFSContentFilterConfig(max_depth=2, include_external= False, max_pages=20, query="", threshold=0.5, allow_domains=None):
    if allow_domains is not None:
        filter_chain  = FilterChain([
             ContentRelevanceFilter(
                query=query,
                threshold=threshold,
                 
             ),
            ContentTypeFilter(allowed_types=["text/html"])
        
        ])
    else:
        filter_chain  = FilterChain([
             ContentRelevanceFilter(
                query=query,
                threshold=threshold
             ),
            ContentTypeFilter(allowed_types=["text/html"])
        
        ])
        
    
    return CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=max_depth, 
            include_external=include_external,
            max_pages=max_pages,
            filter_chain=filter_chain
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS, # fetch each time
        verbose=True,
        stream=False)
    

def generateBFSSEOFilterConfig(max_depth=2, include_external= False, max_pages=20, keywords=[], threshold=0.5):
    filter_chain  = FilterChain([
         SEOFilter(
             threshold=threshold,
             keywords=keywords
         ),
         ContentTypeFilter(allowed_types=["text/html"])
    
    ])
    
    return CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=max_depth, 
            include_external=include_external,
            max_pages=max_pages,
            filter_chain=filter_chain
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS, # fetch each time
        verbose=True,
        stream=False)


def generateBFSKeywordScorerConfig(max_depth=2, include_external= False, max_pages=15, keywords=[], weight=0.7):
    keyword_scorer = KeywordRelevanceScorer(
        keywords=[],
        weight=weight
    )
    filter_chain  = FilterChain([
        ContentTypeFilter(allowed_types=["text/html"])
    
    ])
    return CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=max_depth, 
            include_external=include_external,
            max_pages=max_pages,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS, # fetch each time
        verbose=True,
        stream=False)

    
def generateAdaptiveConfig(confidence_threshold=0.8, max_pages=15, ):
    return AdaptiveConfig(
        strategy="statistical",
        confidence_threshold= confidence_threshold

    )
    


async def getWebPageContent(url, browser_config=browser_config1):
    """
    Fetch the single content of a web page using AsyncWebCrawler.
    """
    async with AsyncWebCrawler() as crawler:
        # Configure the crawler
        result = await crawler.arun(
            url=url,
            browser_config=browser_config,
            run_config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,  # Disable caching
                # max_depth=1,  # Limit the depth of crawling
            )
        )
        return result


async def getWebPageContentsConcurrent(urls, browser_config=browser_config1, 
                                       crawler_config=crawler_config1):
    """
    Fetch the contents of multiple web pages concurrently.
    """
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=95.0,
        check_interval=0.5,
        max_session_permit=5,
        # monitor=CrawlerMonitor(
        #      max_visible_rows=15,
        #     display_mode=DisplayMode.DETAILED
        #     )
        )
    async with AsyncWebCrawler() as crawler:
        # Create a dispatcher for concurrent requests
        try:
            startTime = time.time()
            successCnt = 0
            failureCnt = 0
            rets = [] # aggregate results
            results = await crawler.arun_many(
                urls=urls,
                browser_config=browser_config,
                run_config=crawler_config,
                dispatcher=dispatcher
            )
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error fetching {result.url}: {result.error_message}")
                    failureCnt += 1
                    
                elif result.success:
                    print(f"Successfully fetched : {result.url}")
                    print(f"HTML length: {len(result.html)}")
                    print(f"Markdown length: {len(result.markdown)}")
                    print(f"Markdown snippet : {result.markdown[:200]}...")
                    rets.append(result)
                    successCnt += 1
                else:
                    print(f"Failed to fetch {result.url}: {result.error}")
                    failureCnt += 1
            
            print(f"Total URLs: {len(urls)}, Success: {successCnt}, Failures: {failureCnt}")
            print(f"Time Taken:  {time.time() - startTime}")


        except Exception as e:
            print(f"Error during crawling: {e}")
            results = None
        finally:
            await crawler.close()
        return rets

async def getDeepCraw(url, browser_config=browser_config1, 
                     crawler_config=crawler_config3):
        async with AsyncWebCrawler() as crawler:
        # Create a dispatcher for concurrent requests
            try:
                startTime = time.time()
                successCnt = 0
                failureCnt = 0
                rets = [] # aggregate results
                dispatcher = MemoryAdaptiveDispatcher(
                            memory_threshold_percent=85.0,
                            check_interval=1,
                            max_session_permit=5,
                            # monitor=CrawlerMonitor(
                            #      max_visible_rows=15,
                            #     display_mode=DisplayMode.DETAILED
                            #     )
                )
                
                results = await crawler.arun(
                    url=url,
                    config=crawler_config,
                    # dispatcher=dispatcher
                )
                print(f"Crawled {len(results)} pages in total")
                for result in results:
                    # rets.append(result)
                    if isinstance(result, Exception):
                        print(f"Error fetching {result.url}: {result.error_message}")
                        failureCnt += 1
                        
                    elif result.success:
                        print(f"Successfully fetched : {result.url}")
                        print(f"HTML length: {len(result.html)}")
                        print(f"Markdown length: {len(result.markdown)}")
                        print(f"Markdown snippet : {result.markdown[:200]}...")
                        rets.append(result)
                        successCnt += 1
                    else:
                        print(f"Failed to fetch {result.url}: {result.error_message}")
                        failureCnt += 1
                
                print(f"Total URLs: {url}, Success: {successCnt}, Failures: {failureCnt}")
                print(f"Time Taken:  {time.time() - startTime}")
    
    
            except Exception as e:
                print(f"Error during crawling: {e}")
                results = None
            finally:
                await crawler.close()
        return rets 
    

async def getAdaptiveCraw(url, browser_config=browser_config1, 
                     adaptive_config=None, query=""):
        async with AsyncWebCrawler() as crawler:
        # Create a dispatcher for concurrent requests
            try:
                adaptive = AdaptiveCrawler(crawler, adaptive_config)  # Uses default statistical strategy
                startTime = time.time()
                successCnt = 0
                failureCnt = 0
                rets = [] # aggregate results
                
                results = await adaptive.digest(
                        start_url = url,
                        query=query
                )
                adaptive.print_stats(detailed=True)   # Detailed metrics


                print(f"Crawled {len(results)} pages in total")
                for result in results:
                    # rets.append(result)
                    if isinstance(result, Exception):
                        print(f"Error fetching {result.url}: {result.error_message}")
                        failureCnt += 1
                        
                    elif result.success:
                        print(f"Successfully fetched : {result.url}")
                        print(f"HTML length: {len(result.html)}")
                        print(f"Markdown length: {len(result.markdown)}")
                        print(f"Markdown snippet : {result.markdown[:200]}...")
                        rets.append(result)
                        successCnt += 1
                    else:
                        print(f"Failed to fetch {result.url}: {result.error_message}")
                        failureCnt += 1
                
                print(f"Total URLs: {url}, Success: {successCnt}, Failures: {failureCnt}")
                print(f"Time Taken:  {time.time() - startTime}")
    
    
            except Exception as e:
                print(f"Error during crawling: {e}")
                results = None
            finally:
                await crawler.close()
        return rets 
 