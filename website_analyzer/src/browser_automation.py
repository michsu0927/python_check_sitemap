"""
Browser 自動化模組
使用 browser-use 進行瀏覽器自動化操作，執行頁面截圖和互動測試
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import base64
from PIL import Image
import io

# Browser-use 相關導入
try:
    from browser_use import Browser, BrowserConfig
    from browser_use.browser.browser import BrowserContext
except ImportError:
    # 如果 browser-use 不可用，使用 playwright 作為備用
    from playwright.async_api import async_playwright, Browser as PlaywrightBrowser
    Browser = None
    BrowserConfig = None

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config_manager import config_manager


@dataclass
class ScreenshotInfo:
    """截圖資訊類"""
    url: str
    device_type: str  # desktop, tablet, mobile
    file_path: Path
    viewport_size: Tuple[int, int]
    timestamp: float
    load_time: float
    error: Optional[str] = None
    file_size: Optional[int] = None


@dataclass
class PageMetrics:
    """頁面效能指標"""
    url: str
    load_time: float
    dom_content_loaded: float
    first_paint: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    total_blocking_time: Optional[float] = None


@dataclass
class InteractionResult:
    """互動測試結果"""
    url: str
    test_type: str  # click, scroll, form_fill
    success: bool
    error: Optional[str] = None
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class BrowserAutomation:
    """瀏覽器自動化控制器"""
    
    def __init__(self, headless: bool = True, max_concurrent: int = 3):
        self.browser_config = config_manager.get_browser_config()
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.browser: Optional[Any] = None
        self.playwright = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # 設備配置
        self.device_configs = {
            "desktop": {
                "viewport": self.browser_config.window_size,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "tablet": {
                "viewport": self.browser_config.tablet_size,
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            },
            "mobile": {
                "viewport": self.browser_config.mobile_size,
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
        }
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        await self._cleanup_browser()
    
    async def _initialize_browser(self):
        """初始化瀏覽器"""
        try:
            if Browser and BrowserConfig:
                # 使用 browser-use
                logger.info("使用 browser-use 初始化瀏覽器")
                browser_config = BrowserConfig(
                    headless=self.headless,
                    viewport_width=self.browser_config.window_size[0],
                    viewport_height=self.browser_config.window_size[1]
                )
                self.browser = Browser(config=browser_config)
                await self.browser.start()
            else:
                # 使用 playwright 作為備用
                logger.info("使用 Playwright 初始化瀏覽器")
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
            
            logger.info("瀏覽器初始化成功")
            
        except Exception as e:
            logger.error(f"瀏覽器初始化失敗: {e}")
            raise
    
    async def _cleanup_browser(self):
        """清理瀏覽器資源"""
        try:
            if self.browser:
                if hasattr(self.browser, 'close'):
                    await self.browser.close()
                elif hasattr(self.browser, 'stop'):
                    await self.browser.stop()
            
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("瀏覽器資源清理完成")
            
        except Exception as e:
            logger.error(f"瀏覽器清理失敗: {e}")
    
    async def _create_page_context(self, device_type: str = "desktop") -> Any:
        """建立頁面上下文"""
        device_config = self.device_configs[device_type]
        
        if hasattr(self.browser, 'new_context'):
            # Playwright 方式
            context = await self.browser.new_context(
                viewport={"width": device_config["viewport"][0], "height": device_config["viewport"][1]},
                user_agent=device_config["user_agent"]
            )
            page = await context.new_page()
        else:
            # browser-use 方式 (假設有類似方法)
            page = await self.browser.new_page()
            await page.set_viewport_size(
                width=device_config["viewport"][0],
                height=device_config["viewport"][1]
            )
        
        return page
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _navigate_to_page(self, page: Any, url: str) -> float:
        """導航到頁面並測量加載時間"""
        start_time = time.time()
        
        try:
            # 設置等待條件
            if hasattr(page, 'goto'):
                # Playwright 方式
                await page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=self.browser_config.timeout * 1000
                )
            else:
                # browser-use 方式
                await page.navigate(url)
                await page.wait_for_load_state('domcontentloaded')
            
            # 額外等待確保頁面完全加載
            await asyncio.sleep(self.browser_config.wait_time)
            
            load_time = time.time() - start_time
            logger.debug(f"頁面加載完成: {url} ({load_time:.2f}s)")
            
            return load_time
            
        except Exception as e:
            logger.error(f"頁面導航失敗 {url}: {e}")
            raise
    
    async def _capture_screenshot(self, page: Any, url: str, device_type: str) -> ScreenshotInfo:
        """擷取頁面截圖"""
        timestamp = time.time()
        
        # 生成檔案名稱
        domain = urlparse(url).netloc.replace('.', '_')
        path_part = urlparse(url).path.replace('/', '_').replace('\\', '_')[:50]
        filename = f"{domain}_{path_part}_{device_type}_{int(timestamp)}.png"
        file_path = self.screenshots_dir / filename
        
        try:
            # 確保頁面完全加載
            await asyncio.sleep(1)
            
            # 截圖
            if hasattr(page, 'screenshot'):
                # Playwright 方式
                screenshot_bytes = await page.screenshot(
                    path=str(file_path),
                    full_page=True,
                    type='png'
                )
            else:
                # browser-use 方式
                screenshot_bytes = await page.screenshot(full_page=True)
                with open(file_path, 'wb') as f:
                    f.write(screenshot_bytes)
            
            # 檢查檔案大小
            file_size = file_path.stat().st_size if file_path.exists() else None
            
            viewport_size = self.device_configs[device_type]["viewport"]
            
            screenshot_info = ScreenshotInfo(
                url=url,
                device_type=device_type,
                file_path=file_path,
                viewport_size=viewport_size,
                timestamp=timestamp,
                load_time=0,  # 將在呼叫處設定
                file_size=file_size
            )
            
            logger.info(f"截圖成功: {filename} ({file_size} bytes)")
            return screenshot_info
            
        except Exception as e:
            error_msg = f"截圖失敗: {e}"
            logger.error(f"{url} {error_msg}")
            
            return ScreenshotInfo(
                url=url,
                device_type=device_type,
                file_path=file_path,
                viewport_size=self.device_configs[device_type]["viewport"],
                timestamp=timestamp,
                load_time=0,
                error=error_msg
            )
    
    async def _collect_performance_metrics(self, page: Any, url: str) -> PageMetrics:
        """收集頁面效能指標"""
        try:
            # 基本的效能指標收集
            if hasattr(page, 'evaluate'):
                # Playwright 方式
                metrics = await page.evaluate("""
                    () => {
                        const navigation = performance.getEntriesByType('navigation')[0];
                        const paint = performance.getEntriesByType('paint');
                        
                        return {
                            loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
                            domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
                            firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || null,
                            firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null
                        };
                    }
                """)
                
                return PageMetrics(
                    url=url,
                    load_time=metrics.get('loadTime', 0) / 1000,
                    dom_content_loaded=metrics.get('domContentLoaded', 0) / 1000,
                    first_paint=metrics.get('firstPaint'),
                    first_contentful_paint=metrics.get('firstContentfulPaint')
                )
            else:
                # 簡化版本
                return PageMetrics(
                    url=url,
                    load_time=0,
                    dom_content_loaded=0
                )
                
        except Exception as e:
            logger.error(f"效能指標收集失敗 {url}: {e}")
            return PageMetrics(url=url, load_time=0, dom_content_loaded=0)
    
    async def _test_basic_interactions(self, page: Any, url: str) -> List[InteractionResult]:
        """測試基本互動功能"""
        results = []
        
        try:
            # 測試頁面滾動
            scroll_result = await self._test_scroll(page, url)
            results.append(scroll_result)
            
            # 測試點擊互動
            click_result = await self._test_clicks(page, url)
            results.append(click_result)
            
            # 測試表單互動 (如果有)
            form_result = await self._test_forms(page, url)
            if form_result:
                results.append(form_result)
            
        except Exception as e:
            logger.error(f"互動測試失敗 {url}: {e}")
            results.append(InteractionResult(
                url=url,
                test_type="interaction_test",
                success=False,
                error=str(e)
            ))
        
        return results
    
    async def _test_scroll(self, page: Any, url: str) -> InteractionResult:
        """測試頁面滾動"""
        try:
            start_time = time.time()
            
            if hasattr(page, 'evaluate'):
                # 滾動到頁面底部
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                
                # 滾動回頂部
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
            
            response_time = time.time() - start_time
            
            return InteractionResult(
                url=url,
                test_type="scroll",
                success=True,
                response_time=response_time
            )
            
        except Exception as e:
            return InteractionResult(
                url=url,
                test_type="scroll",
                success=False,
                error=str(e)
            )
    
    async def _test_clicks(self, page: Any, url: str) -> InteractionResult:
        """測試點擊互動"""
        try:
            start_time = time.time()
            clickable_elements = 0
            
            if hasattr(page, 'query_selector_all'):
                # 尋找可點擊元素
                buttons = await page.query_selector_all('button, a, [onclick], [role="button"]')
                clickable_elements = len(buttons)
                
                # 測試點擊第一個可見按鈕 (如果有)
                for button in buttons[:3]:  # 只測試前 3 個
                    try:
                        is_visible = await button.is_visible()
                        if is_visible:
                            await button.click(timeout=5000)
                            await asyncio.sleep(0.5)
                            break
                    except:
                        continue
            
            response_time = time.time() - start_time
            
            return InteractionResult(
                url=url,
                test_type="click",
                success=True,
                response_time=response_time,
                details={"clickable_elements": clickable_elements}
            )
            
        except Exception as e:
            return InteractionResult(
                url=url,
                test_type="click",
                success=False,
                error=str(e)
            )
    
    async def _test_forms(self, page: Any, url: str) -> Optional[InteractionResult]:
        """測試表單互動"""
        try:
            if hasattr(page, 'query_selector_all'):
                forms = await page.query_selector_all('form')
                if not forms:
                    return None
                
                start_time = time.time()
                form_inputs = 0
                
                # 測試第一個表單
                form = forms[0]
                inputs = await form.query_selector_all('input[type="text"], input[type="email"], textarea')
                form_inputs = len(inputs)
                
                # 嘗試填寫測試資料
                for input_elem in inputs[:3]:  # 只測試前 3 個欄位
                    try:
                        input_type = await input_elem.get_attribute('type') or 'text'
                        test_value = "test@example.com" if input_type == "email" else "test input"
                        await input_elem.fill(test_value)
                        await asyncio.sleep(0.2)
                    except:
                        continue
                
                response_time = time.time() - start_time
                
                return InteractionResult(
                    url=url,
                    test_type="form_fill",
                    success=True,
                    response_time=response_time,
                    details={"form_inputs": form_inputs}
                )
                
        except Exception as e:
            return InteractionResult(
                url=url,
                test_type="form_fill",
                success=False,
                error=str(e)
            )
        
        return None
    
    async def capture_page_screenshots(self, urls: List[str], device_types: List[str] = None) -> List[ScreenshotInfo]:
        """批量擷取頁面截圖"""
        if device_types is None:
            device_types = ["desktop", "tablet", "mobile"]
        
        analysis_config = config_manager.get_analysis_config()
        max_pages = min(len(urls), analysis_config.max_pages)
        urls = urls[:max_pages]
        
        logger.info(f"開始批量截圖: {len(urls)} URLs x {len(device_types)} 設備")
        
        screenshots = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def capture_url_screenshots(url: str) -> List[ScreenshotInfo]:
            async with semaphore:
                url_screenshots = []
                
                for device_type in device_types:
                    try:
                        page = await self._create_page_context(device_type)
                        
                        try:
                            load_time = await self._navigate_to_page(page, url)
                            screenshot_info = await self._capture_screenshot(page, url, device_type)
                            screenshot_info.load_time = load_time
                            url_screenshots.append(screenshot_info)
                            
                        finally:
                            if hasattr(page, 'close'):
                                await page.close()
                            elif hasattr(page, 'context') and hasattr(page.context, 'close'):
                                await page.context.close()
                        
                    except Exception as e:
                        logger.error(f"截圖失敗 {url} ({device_type}): {e}")
                        url_screenshots.append(ScreenshotInfo(
                            url=url,
                            device_type=device_type,
                            file_path=Path(""),
                            viewport_size=self.device_configs[device_type]["viewport"],
                            timestamp=time.time(),
                            load_time=0,
                            error=str(e)
                        ))
                
                return url_screenshots
        
        # 並行處理所有 URLs
        tasks = [capture_url_screenshots(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集結果
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量截圖異常: {result}")
                continue
            screenshots.extend(result)
        
        successful_screenshots = [s for s in screenshots if not s.error]
        logger.info(f"截圖完成: {len(successful_screenshots)}/{len(screenshots)} 成功")
        
        return screenshots
    
    async def analyze_pages_comprehensive(self, urls: List[str]) -> Dict[str, Any]:
        """全面分析頁面 (截圖 + 效能 + 互動測試)"""
        logger.info(f"開始全面頁面分析: {len(urls)} URLs")
        
        analysis_config = config_manager.get_analysis_config()
        max_pages = min(len(urls), analysis_config.max_pages)
        urls = urls[:max_pages]
        
        results = {
            "screenshots": [],
            "performance_metrics": [],
            "interaction_results": [],
            "summary": {}
        }
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def analyze_single_page(url: str) -> Dict[str, Any]:
            async with semaphore:
                page_result = {
                    "url": url,
                    "screenshots": [],
                    "metrics": None,
                    "interactions": [],
                    "error": None
                }
                
                try:
                    page = await self._create_page_context("desktop")
                    
                    try:
                        # 導航到頁面
                        load_time = await self._navigate_to_page(page, url)
                        
                        # 擷取桌面截圖
                        desktop_screenshot = await self._capture_screenshot(page, url, "desktop")
                        desktop_screenshot.load_time = load_time
                        page_result["screenshots"].append(desktop_screenshot)
                        
                        # 收集效能指標
                        metrics = await self._collect_performance_metrics(page, url)
                        metrics.load_time = load_time
                        page_result["metrics"] = metrics
                        
                        # 互動測試
                        interactions = await self._test_basic_interactions(page, url)
                        page_result["interactions"] = interactions
                        
                    finally:
                        if hasattr(page, 'close'):
                            await page.close()
                        elif hasattr(page, 'context') and hasattr(page.context, 'close'):
                            await page.context.close()
                
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"頁面分析失敗 {url}: {error_msg}")
                    page_result["error"] = error_msg
                
                return page_result
        
        # 並行分析所有頁面
        tasks = [analyze_single_page(url) for url in urls]
        page_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理結果
        successful_analyses = 0
        total_load_time = 0
        
        for result in page_results:
            if isinstance(result, Exception):
                logger.error(f"頁面分析異常: {result}")
                continue
            
            if not result.get("error"):
                successful_analyses += 1
                if result.get("metrics") and result["metrics"].load_time:
                    total_load_time += result["metrics"].load_time
            
            # 收集到全域結果
            results["screenshots"].extend(result.get("screenshots", []))
            if result.get("metrics"):
                results["performance_metrics"].append(result["metrics"])
            results["interaction_results"].extend(result.get("interactions", []))
        
        # 生成摘要
        results["summary"] = {
            "total_pages": len(urls),
            "successful_analyses": successful_analyses,
            "success_rate": successful_analyses / len(urls) if urls else 0,
            "average_load_time": total_load_time / successful_analyses if successful_analyses > 0 else 0,
            "total_screenshots": len([s for s in results["screenshots"] if not s.error]),
            "total_interactions_tested": len(results["interaction_results"])
        }
        
        logger.info(f"全面分析完成: {successful_analyses}/{len(urls)} 成功")
        return results
