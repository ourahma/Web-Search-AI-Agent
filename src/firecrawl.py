import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv
load_dotenv()

class FireCrawlService:
    def __init__(self):
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise EnvironmentError('FIRECRAWL_API_KEY is not set')

        self.app = FirecrawlApp(api_key)

    def search_companies(self,query,num_results: int = 5):
        try :
            result = self.app.search(
                query=f"{query} Company pricing",
                limit=num_results,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return result
        except Exception as e:
            print('$'*100)
            print(e)
            return []

    def scrap_company_pages(self,url:str):
        try:
            result = self.app.scrape_url(
                url=url,
                formats=["markdown"]
            )
            return result
        except Exception as e:
            print('$'*100)
            print(e)

            return None


