import requests
import logging
import re

from bs4 import BeautifulSoup as bs

from typing import Dict, List, Optional
import urllib.parse as urlparse

from app.helper import Helper


logging.basicConfig(
    format='{levelname:<10} {asctime}: {message}', 
    level=logging.INFO, 
    datefmt='%m/%d/%Y %H:%M:%S',
    style='{')
logger = logging.getLogger(__name__)

class Crawler():
    """
    Generic class defining crawler.
    """
    def __init__(self):
        self.URL_MAIN = 'https://www.inform.kz'
        self.URL_ARCHIVE = 'https://www.inform.kz/ru/archive'
        self.session = requests.Session()

    def get_url(self, url: str, params: Dict[str, str] = None) -> requests.Response:
        """
        Fetch the URL provided and return response object.

        Args:
            url (str): URL provided.
            params (Dict[str, str]): query parameters in dictinary format.

        Returns:
            requests.Response: HTML page fetched with response code.
        """
        try:
            r = self.session.get(url, params = params)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(Helper._message(f'Failed to get the URL {r.url}', e))
            raise SystemExit(e)
        logger.info(Helper._message(f'Success retrieving URL {r.url}'))
        return r

    def _extract_links(self, response: requests.Response) -> List[str]:
        """
        Retrieving links given the response object.

        Args:
            body (requests.Response): response object containing links to articles.

        Returns:
            List[str]: list of extractred article links give the reponse.
        """
        soup = bs(response.content, 'html.parser')
        link_divs = soup.find_all('div', class_ = 'lenta_news_block')
        try:
            links = [d.li.a['href'].strip() for d in link_divs]
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to extract links to articles at {response.url}.', e))
            raise SystemExit(e)
        logger.info(Helper._message(f'Retrieved article links from {response.url} successfully.'))
        return [urlparse.urlparse(self.URL_MAIN + l).geturl() for l in links]
    
    def _extract_pages(self, response: requests.Response) -> List[str]:
        """
        Retrieving article page links from first page for the some particular date.
        Note: call this function for the first page from particular date to retieve the article pages
        for that particular date. 

        Args:
            response (requests.Response): response object of the first page.

        Returns:
            List[str]: links for the article pages.
        """
        soup = bs(response.content, 'html.parser')
        try:
            pages = soup.find('p', class_ = 'pagination')
            pages = pages.find_all('a')
            pi = pages[0].getText().strip()
            pl = pages[-1].getText().strip()
            parsed_url = urlparse.urlparse(response.url)
            pages = [parsed_url._replace(path=f'/ru/archive/{str(i)}').geturl() for i in range(int(pi), int(pl) + 1)]
        except (AttributeError, IndexError, ValueError, TypeError) as e:
            logger.error(Helper._message(f'Failed to fetch articles page links at URL {response.url}', e))
            raise SystemExit(e)
        logger.info(Helper._message(f'Retrieved article page links from {response.url} successfully'))
        return pages

    def get_links(self, response: requests.Response) -> List[str]:
        """
        Get the list of URLs for the articles given the response object from particular URL of specific date.

        Args:
            response (requests.Response): response object of the first page.

        Returns:
            List[str]: list of URLs for articles for the specific date.
        """
        articles = self._extract_links(response)
        for l in self._extract_pages(response):
            r = self.get_url(l)
            articles.extend(self._extract_links(r))
        return articles
        
    def _get_title(self, soup: bs, url: str) -> str:
        """
        Get the title of the article from BS object.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            str: title of the article.
        """
        try:
            title = soup.find('div', class_ = 'article_title')
            title = title.getText().strip()
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch title at URL {url}', e))
            raise SystemExit(e)
        return title
    
    def _get_date(self, soup: bs, url: str) -> str:
        """
        Get the date of the article from BS object.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            str: date of the article.
        """
        try:
            date = soup.find('div', class_ = 'date_public_art')
            date = date.getText().strip()
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch date at URL {url}', e))
            raise SystemExit(e)
        return date
    
    def _get_links(self, soup: bs, url: str) -> List[str]:
        """
        Get the links of related articles from BS object.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            List[str]: List of links. Return 0 elements if no links.
        """
        try:
            links = soup.find('div', class_ = 'frame_news_article')
            res = set()
            if links:
                for a in links.find_all('a'):
                    res.add(a['href'])
                links.decompose()
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch links at URL {url}', e))
            raise SystemExit(e)
        return list(res)
    
    def _decompose_quotes(self, soup: bs, url: str) -> None:
        """
        Decomposes some elements for clear retrieval of the article body.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).
        """
        try:
            quotes = soup.find_all('blockquote', class_ = 'instagram-media')
            if quotes:
                for q in quotes:
                    q.decompose()
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to decompase quotes at URL {url}', e))
            raise SystemExit(e)
               
    def _get_body(self, soup: bs, url: str) -> str:
        """
        Get the article body from BS object.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            str: Article body (text).
        """
        try:
            body = soup.find('div', class_ = 'article_news_body')
            body = body.getText().strip()
            body = re.sub(' +', ' ', body)
            body = re.sub('\r', '\n', body)
            body = re.sub('\n +', '\n', body)
            body = re.sub(' +\n', '\n', body)
            body = re.sub('\n+', '\n', body)
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch the body text at {url}', e))
            raise SystemExit(e)
        return body

    def _get_keywords(self, soup: bs, url: str) -> List[str]:
        """
        Get the keywords for the article from BS object. It is assumed that articles is always with keywords.
        (FIX IF NEEDED)

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            List[str]: List of keywords.
        """
        try:
            keywords = soup.find('div', class_ = 'keyword_art')
            keywords = [t.strip() for t in keywords.getText().split('#') if len(t.strip()) > 0]
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch keywords at URL {url}', e))
            raise SystemExit(e)
        return keywords

    def _get_author(self, soup: bs, url: str) -> Optional[str]:
        """
        Get the author of the article if exists from BS object.

        Args:
            soup (bs): BS object.
            url (str): URL of the article (for reporting exceptions).

        Returns:
            Optional[str]: Return author (text) or None.
        """
        try:
            author = soup.find('p', class_ = 'name_p')
            if author:
                author = author.getText().strip()
        except AttributeError as e:
            logger.error(Helper._message(f'Failed to fetch author at URL {url}', e))
            raise SystemExit(e)
        return author
            
            
    def extract_article(self, response: requests.Response) -> Dict[str, str]:
        """
        Retrieving article data given the response from article URL.

        Args:
            response (requests.Response): response object of the article URL.

        Returns:
            Dict[str, str]: Dictionary with elements of the article.
        """
        soup = bs(response.content, 'html.parser')
        res = {}
        res['url'] = response.url
        
        title = self._get_title(soup, response.url)
        date = self._get_date(soup, response.url)
        links = self._get_links(soup, response.url)
        self._decompose_quotes(soup, response.url)
        body = self._get_body(soup, response.url)
        keywords = self._get_keywords(soup, response.url)
        author = self._get_author(soup, response.url)

        res['title'] = title
        res['date'] = date
        if len(links) > 0: res['links'] = links
        res['body'] = body
        if len(keywords) > 0: res['keywords'] = keywords
        if author: res['author'] = author
        logger.info(Helper._message(f'Success retrieving article at URL: {response.url}'))

        return res