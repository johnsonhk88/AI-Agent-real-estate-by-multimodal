from utils.utils import set_log_level
import os , json, time , gc
import logging


# Crawl4AI is a web crawling and data extraction library designed for AI applications.

from crawl4ai import  AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import crawl4ai


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



# define browser configuration
browser_config1= BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    # for better performance in Docker or low memory menivroment 
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

crawler_config1 = CrawlerRunConfig(
            # fetch_ssl_certificate=True,
            word_count_threshold=10, 
            excluded_tags=["form", "header"],
            exclude_external_links=True,
    
            markdown_generator=DefaultMarkdownGenerator(),
            # Content processing
            process_iframes=True,
            remove_overlay_elements=True,

            # Cache control 
            # cache_mode=CacheMode.ENABLED,
            cache_mode=CacheMode.BYPASS,  # fetch each time
    
            page_timeout=120000,  #60000, #30000, # for each image 
            wait_for_images=True,
            verbose=True,
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