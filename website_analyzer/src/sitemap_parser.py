"""
Sitemap 解析模組
解析網站 sitemap.xml，提取所有 URL，支援嵌套 sitemap 和 sitemap index
"""

import asyncio
import aiohttp
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class URLInfo:
    """URL 資訊類"""
    url: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None
    loc_type: str = "page"  # page, image, video, news
    source_sitemap: Optional[str] = None


@dataclass
class SitemapInfo:
    """Sitemap 資訊類"""
    url: str
    urls: List[URLInfo]
    nested_sitemaps: List[str]
    last_parsed: float
    error: Optional[str] = None


class SitemapParser:
    """Sitemap 解析器"""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.parsed_sitemaps: Set[str] = set()
        self.all_urls: List[URLInfo] = []
        
    async def __aenter__(self):
        """異步上下文管理器進入"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Website-Analyzer-Bot/1.0 (Sitemap Parser)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """標準化 URL"""
        if url.startswith('http'):
            return url
        return urljoin(base_url, url)
    
    def _get_domain(self, url: str) -> str:
        """取得域名"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _discover_sitemap_urls(self, domain: str) -> List[str]:
        """發現可能的 sitemap URL"""
        common_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps.xml',
            '/sitemap/sitemap.xml',
            '/wp-sitemap.xml',
            '/sitemap1.xml'
        ]
        
        return [urljoin(domain, path) for path in common_paths]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_content(self, url: str) -> Optional[str]:
        """獲取 URL 內容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"成功獲取內容: {url}")
                    return content
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"獲取內容失敗 {url}: {e}")
            raise
    
    def _parse_sitemap_xml(self, content: str, sitemap_url: str) -> Tuple[List[URLInfo], List[str]]:
        """解析 sitemap XML 內容"""
        try:
            soup = BeautifulSoup(content, 'xml')
            urls = []
            nested_sitemaps = []
            
            # 檢查是否為 sitemap index
            if soup.find('sitemapindex'):
                # 這是一個 sitemap index，包含其他 sitemap 的引用
                for sitemap in soup.find_all('sitemap'):
                    loc = sitemap.find('loc')
                    if loc and loc.text:
                        nested_sitemaps.append(loc.text.strip())
                        logger.info(f"發現嵌套 sitemap: {loc.text.strip()}")
            
            # 解析 URL 條目
            for url_elem in soup.find_all('url'):
                loc = url_elem.find('loc')
                if loc and loc.text:
                    url_info = URLInfo(
                        url=loc.text.strip(),
                        source_sitemap=sitemap_url
                    )
                    
                    # 提取可選元素
                    lastmod = url_elem.find('lastmod')
                    if lastmod and lastmod.text:
                        url_info.lastmod = lastmod.text.strip()
                    
                    changefreq = url_elem.find('changefreq')
                    if changefreq and changefreq.text:
                        url_info.changefreq = changefreq.text.strip()
                    
                    priority = url_elem.find('priority')
                    if priority and priority.text:
                        try:
                            url_info.priority = float(priority.text.strip())
                        except ValueError:
                            pass
                    
                    urls.append(url_info)
            
            # 解析其他類型的 sitemap (image, video, news)
            for image in soup.find_all('image:image'):
                loc = image.find('image:loc')
                if loc and loc.text:
                    urls.append(URLInfo(
                        url=loc.text.strip(),
                        loc_type="image",
                        source_sitemap=sitemap_url
                    ))
            
            logger.info(f"解析 sitemap {sitemap_url}: {len(urls)} URLs, {len(nested_sitemaps)} 嵌套 sitemaps")
            return urls, nested_sitemaps
            
        except Exception as e:
            logger.error(f"解析 sitemap XML 失敗 {sitemap_url}: {e}")
            return [], []
    
    async def _parse_single_sitemap(self, sitemap_url: str) -> SitemapInfo:
        """解析單一 sitemap"""
        if sitemap_url in self.parsed_sitemaps:
            logger.debug(f"Sitemap 已解析過: {sitemap_url}")
            return SitemapInfo(sitemap_url, [], [], time.time())
        
        self.parsed_sitemaps.add(sitemap_url)
        
        try:
            content = await self._fetch_content(sitemap_url)
            if not content:
                return SitemapInfo(
                    sitemap_url, [], [], time.time(), 
                    error="無法獲取內容"
                )
            
            urls, nested_sitemaps = self._parse_sitemap_xml(content, sitemap_url)
            
            return SitemapInfo(
                url=sitemap_url,
                urls=urls,
                nested_sitemaps=nested_sitemaps,
                last_parsed=time.time()
            )
            
        except Exception as e:
            error_msg = f"解析失敗: {e}"
            logger.error(f"Sitemap {sitemap_url} {error_msg}")
            return SitemapInfo(
                sitemap_url, [], [], time.time(), 
                error=error_msg
            )
    
    async def _check_robots_txt(self, domain: str) -> List[str]:
        """檢查 robots.txt 中的 sitemap 聲明"""
        robots_url = urljoin(domain, '/robots.txt')
        sitemaps = []
        
        try:
            content = await self._fetch_content(robots_url)
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line[8:].strip()
                        if sitemap_url:
                            sitemaps.append(sitemap_url)
                            logger.info(f"從 robots.txt 發現 sitemap: {sitemap_url}")
        except Exception as e:
            logger.debug(f"無法讀取 robots.txt {robots_url}: {e}")
        
        return sitemaps
    
    async def parse_website(self, website_url: str, max_depth: int = 3) -> List[URLInfo]:
        """解析網站的所有 sitemap"""
        domain = self._get_domain(website_url)
        logger.info(f"開始解析網站 sitemap: {domain}")
        
        # 重置狀態
        self.parsed_sitemaps.clear()
        self.all_urls.clear()
        
        # 發現 sitemap URLs
        sitemap_urls = set()
        
        # 1. 從 robots.txt 發現
        robots_sitemaps = await self._check_robots_txt(domain)
        sitemap_urls.update(robots_sitemaps)
        
        # 2. 常見路徑發現
        common_sitemaps = self._discover_sitemap_urls(domain)
        sitemap_urls.update(common_sitemaps)
        
        # 如果沒有發現任何 sitemap，嘗試主要的
        if not sitemap_urls:
            sitemap_urls.add(urljoin(domain, '/sitemap.xml'))
        
        # 解析所有發現的 sitemap
        pending_sitemaps = list(sitemap_urls)
        depth = 0
        
        while pending_sitemaps and depth < max_depth:
            logger.info(f"解析深度 {depth + 1}: {len(pending_sitemaps)} sitemaps")
            
            # 並行解析當前層的所有 sitemap
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def parse_with_semaphore(url):
                async with semaphore:
                    return await self._parse_single_sitemap(url)
            
            tasks = [parse_with_semaphore(url) for url in pending_sitemaps]
            sitemap_infos = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            next_level_sitemaps = []
            for i, result in enumerate(sitemap_infos):
                if isinstance(result, Exception):
                    logger.error(f"解析 sitemap 異常 {pending_sitemaps[i]}: {result}")
                    continue
                
                sitemap_info = result
                if sitemap_info.error:
                    logger.warning(f"Sitemap 解析錯誤: {sitemap_info.error}")
                    continue
                
                # 收集 URLs
                self.all_urls.extend(sitemap_info.urls)
                
                # 收集下一層的 sitemaps
                for nested_url in sitemap_info.nested_sitemaps:
                    normalized_url = self._normalize_url(nested_url, domain)
                    if normalized_url not in self.parsed_sitemaps:
                        next_level_sitemaps.append(normalized_url)
            
            pending_sitemaps = next_level_sitemaps
            depth += 1
        
        # 去重和過濾
        unique_urls = self._deduplicate_urls(self.all_urls)
        filtered_urls = self._filter_urls(unique_urls, domain)
        
        logger.info(f"解析完成: 發現 {len(filtered_urls)} 個有效 URLs")
        return filtered_urls
    
    def _deduplicate_urls(self, urls: List[URLInfo]) -> List[URLInfo]:
        """URL 去重"""
        seen_urls = set()
        unique_urls = []
        
        for url_info in urls:
            if url_info.url not in seen_urls:
                seen_urls.add(url_info.url)
                unique_urls.append(url_info)
        
        logger.info(f"去重: {len(urls)} -> {len(unique_urls)} URLs")
        return unique_urls
    
    def _filter_urls(self, urls: List[URLInfo], domain: str) -> List[URLInfo]:
        """過濾和分類 URLs"""
        filtered_urls = []
        domain_netloc = urlparse(domain).netloc
        
        # 過濾規則
        exclude_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', 
                            '.css', '.js', '.ico', '.xml', '.txt', '.zip'}
        exclude_patterns = {'admin', 'wp-admin', 'login', 'register', 'api/'}
        
        for url_info in urls:
            parsed_url = urlparse(url_info.url)
            
            # 只保留同域名的 URL
            if parsed_url.netloc != domain_netloc:
                continue
            
            # 排除特定副檔名
            path_lower = parsed_url.path.lower()
            if any(path_lower.endswith(ext) for ext in exclude_extensions):
                continue
            
            # 排除特定模式
            if any(pattern in path_lower for pattern in exclude_patterns):
                continue
            
            # 排除過長的 URL (可能是動態生成的)
            if len(url_info.url) > 200:
                continue
            
            filtered_urls.append(url_info)
        
        # 按優先級排序
        filtered_urls.sort(key=self._get_url_priority, reverse=True)
        
        logger.info(f"過濾: {len(urls)} -> {len(filtered_urls)} URLs")
        return filtered_urls
    
    def _get_url_priority(self, url_info: URLInfo) -> float:
        """計算 URL 優先級"""
        priority = url_info.priority or 0.5
        
        # 根據 URL 路徑調整優先級
        path = urlparse(url_info.url).path.lower()
        
        # 首頁最高優先級
        if path in ['', '/']:
            priority += 0.5
        
        # 主要頁面較高優先級
        if any(keyword in path for keyword in ['about', 'service', 'product', 'contact']):
            priority += 0.2
        
        # 深層頁面較低優先級
        depth = len([p for p in path.split('/') if p])
        priority -= depth * 0.1
        
        return min(1.0, max(0.0, priority))
    
    def categorize_urls(self, urls: List[URLInfo]) -> Dict[str, List[URLInfo]]:
        """分類 URLs"""
        categories = {
            'homepage': [],
            'main_pages': [],
            'content_pages': [],
            'category_pages': [],
            'product_pages': [],
            'other': []
        }
        
        for url_info in urls:
            path = urlparse(url_info.url).path.lower()
            
            if path in ['', '/']:
                categories['homepage'].append(url_info)
            elif any(keyword in path for keyword in ['about', 'service', 'contact', 'help']):
                categories['main_pages'].append(url_info)
            elif any(keyword in path for keyword in ['product', 'item', 'detail']):
                categories['product_pages'].append(url_info)
            elif any(keyword in path for keyword in ['category', 'tag', 'archive']):
                categories['category_pages'].append(url_info)
            elif any(keyword in path for keyword in ['blog', 'news', 'article']):
                categories['content_pages'].append(url_info)
            else:
                categories['other'].append(url_info)
        
        # 記錄分類統計
        for category, url_list in categories.items():
            if url_list:
                logger.info(f"分類 {category}: {len(url_list)} URLs")
        
        return categories


# 同步版本的簡化解析器
class SimpleSitemapParser:
    """簡化的同步 sitemap 解析器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Website-Analyzer-Bot/1.0 (Sitemap Parser)'
        })
    
    def parse_sitemap_simple(self, website_url: str) -> List[str]:
        """簡單解析 sitemap，只返回 URL 列表"""
        domain = urlparse(website_url).scheme + "://" + urlparse(website_url).netloc
        sitemap_url = urljoin(domain, '/sitemap.xml')
        
        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                urls = []
                
                for url_elem in soup.find_all('url'):
                    loc = url_elem.find('loc')
                    if loc and loc.text:
                        urls.append(loc.text.strip())
                
                logger.info(f"簡單解析發現 {len(urls)} URLs")
                return urls[:50]  # 限制數量
            
        except Exception as e:
            logger.error(f"簡單解析失敗 {sitemap_url}: {e}")
        
        return []
