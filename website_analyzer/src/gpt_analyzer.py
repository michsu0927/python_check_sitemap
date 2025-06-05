"""
GPT 分析引擎模組
使用 GPT-4 Vision API 分析網頁截圖，支援 Azure OpenAI 和標準 OpenAI API
"""

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from PIL import Image
import io

# API 客戶端導入
try:
    from openai import AsyncOpenAI
    from openai import AsyncAzureOpenAI
except ImportError as e:
    print(f"警告: 部分 AI 套件未安裝: {e}")
    AsyncOpenAI = None
    AsyncAzureOpenAI = None

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config_manager import config_manager
from .browser_automation import ScreenshotInfo


@dataclass
class AnalysisResult:
    """分析結果類"""
    url: str
    device_type: str
    timestamp: float
    
    # 視覺設計分析
    visual_design_score: float  # 0-10
    color_scheme_rating: float
    typography_rating: float
    layout_balance_rating: float
    brand_consistency: float
    
    # 用戶體驗評估
    ux_score: float  # 0-10
    navigation_clarity: float
    content_readability: float
    cta_effectiveness: float
    mobile_responsiveness: float
    
    # 技術品質檢查
    technical_score: float  # 0-10
    page_structure: float
    accessibility_rating: float
    performance_impact: float
    
    # 內容品質分析
    content_score: float  # 0-10
    content_relevance: float
    seo_optimization: float
    multimedia_usage: float
    
    # 整體評分和建議
    overall_score: float  # 0-10
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    # 元數據
    analysis_confidence: float  # 0-1
    processing_time: float
    error: Optional[str] = None


class GPTAnalyzer:
    """GPT 圖像分析引擎"""
    
    def __init__(self):
        self.config = config_manager.get_api_config()
        self.client: Optional[AsyncOpenAI] = None
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.request_count = 0
        self.total_tokens = 0
        
        # 分析提示詞模板
        self.analysis_prompt = self._create_analysis_prompt()
        
    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self._initialize_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.client:
            await self.client.close()
    
    async def _initialize_client(self):
        """初始化 API 客戶端"""
        try:
            if self.config.service == "azure_openai":
                # Azure OpenAI 配置 - 使用新的 AsyncAzureOpenAI 類
                logger.info("初始化 Azure OpenAI 客戶端")
                self.client = AsyncAzureOpenAI(
                    api_key=self.config.api_key,
                    api_version=self.config.api_version,
                    azure_endpoint=self.config.endpoint
                )
            else:
                # 標準 OpenAI 配置
                logger.info("初始化 OpenAI 客戶端")
                self.client = AsyncOpenAI(api_key=self.config.api_key)
            
            # 驗證連接
            if not await self._test_connection():
                raise Exception("API 連接測試失敗")
            
            logger.info("GPT 分析引擎初始化成功")
            
        except Exception as e:
            logger.error(f"GPT 分析引擎初始化失敗: {e}")
            raise
    
    async def _test_connection(self) -> bool:
        """測試 API 連接"""
        try:
            # 簡單的測試請求
            test_messages = [
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            
            if self.config.service == "azure_openai":
                response = await self.client.chat.completions.create(
                    model=self.config.deployment_name,
                    messages=test_messages,
                    max_tokens=10
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=test_messages,
                    max_tokens=10
                )
            
            return bool(response.choices)
            
        except Exception as e:
            logger.error(f"API 連接測試失敗: {e}")
            return False
    
    def _create_analysis_prompt(self) -> str:
        """建立分析提示詞"""
        return """
你是一位專業的網站 UX/UI 設計和數位營銷專家。請分析這個網頁截圖，從以下四個維度進行詳細評估：

## 分析維度 (請為每個項目提供 0-10 的評分)

### 1. 視覺設計分析 (Visual Design)
- 色彩搭配和品牌一致性 (0-10)
- 排版和視覺層次 (0-10)
- 版面平衡和美感 (0-10)
- 品牌識別度 (0-10)

### 2. 用戶體驗評估 (User Experience)
- 導航結構清晰度 (0-10)
- 內容可讀性 (0-10)
- 行動號召按鈕效果 (0-10)
- 響應式設計實現 (0-10)

### 3. 技術品質檢查 (Technical Quality)
- 頁面結構組織 (0-10)
- 可訪問性實現 (0-10)
- 頁面加載速度影響 (0-10)

### 4. 內容品質分析 (Content Quality)
- 文字內容相關性和價值 (0-10)
- SEO 優化程度 (0-10)
- 多媒體使用效果 (0-10)

## 輸出格式
請以 JSON 格式回應，包含以下結構：

```json
{
    "visual_design": {
        "score": 8.5,
        "color_scheme": 9.0,
        "typography": 8.0,
        "layout_balance": 8.5,
        "brand_consistency": 8.5
    },
    "user_experience": {
        "score": 7.5,
        "navigation_clarity": 8.0,
        "content_readability": 7.5,
        "cta_effectiveness": 7.0,
        "mobile_responsiveness": 7.5
    },
    "technical_quality": {
        "score": 7.0,
        "page_structure": 7.5,
        "accessibility": 6.5,
        "performance_impact": 7.0
    },
    "content_quality": {
        "score": 8.0,
        "content_relevance": 8.5,
        "seo_optimization": 7.5,
        "multimedia_usage": 8.0
    },
    "overall": {
        "score": 7.8,
        "confidence": 0.85
    },
    "analysis": {
        "strengths": [
            "色彩搭配協調，符合品牌調性",
            "內容層次分明，易於閱讀",
            "主要功能按鈕位置突出"
        ],
        "weaknesses": [
            "導航結構可以更加清晰",
            "部分文字內容過於密集",
            "缺少明確的行動號召"
        ],
        "recommendations": [
            "優化導航選單的視覺設計",
            "增加適當的留白空間",
            "強化主要轉換按鈕的視覺效果",
            "考慮添加更多互動元素"
        ]
    }
}
```

請確保：
1. 所有評分都在 0-10 範圍內
2. 提供具體且可操作的建議
3. 分析基於實際觀察到的設計元素
4. 考慮現代網頁設計最佳實踐
"""
    
    def _optimize_image(self, image_path: Path, max_size: Tuple[int, int] = (1024, 768)) -> str:
        """優化圖片並轉換為 base64"""
        try:
            with Image.open(image_path) as img:
                # 轉換為 RGB (如果需要)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 調整大小
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 轉換為 base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                image_data = buffer.getvalue()
                
                base64_string = base64.b64encode(image_data).decode('utf-8')
                
                logger.debug(f"圖片優化完成: {image_path.name} -> {len(base64_string)} chars")
                return base64_string
                
        except Exception as e:
            logger.error(f"圖片優化失敗 {image_path}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
    async def _call_vision_api(self, image_base64: str, url: str, device_type: str) -> Dict[str, Any]:
        """呼叫 Vision API 進行分析"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{self.analysis_prompt}\n\n網頁 URL: {url}\n設備類型: {device_type}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # API 請求參數
            api_params = {
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            if self.config.service == "azure_openai":
                api_params["model"] = self.config.deployment_name
            else:
                api_params["model"] = self.config.model
            
            # 發送請求
            start_time = time.time()
            response = await self.client.chat.completions.create(**api_params)
            processing_time = time.time() - start_time
            
            # 更新統計
            self.request_count += 1
            if hasattr(response, 'usage') and response.usage:
                self.total_tokens += response.usage.total_tokens
            
            # 解析回應
            content = response.choices[0].message.content
            
            # 嘗試提取 JSON
            try:
                # 尋找 JSON 內容
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    result = json.loads(json_content)
                    result['_processing_time'] = processing_time
                    result['_raw_response'] = content
                    return result
                else:
                    raise ValueError("未找到有效的 JSON 回應")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失敗: {e}")
                logger.debug(f"原始回應: {content}")
                raise ValueError(f"API 回應格式錯誤: {e}")
            
        except Exception as e:
            logger.error(f"Vision API 呼叫失敗 {url}: {e}")
            raise
    
    def _parse_api_response(self, api_response: Dict[str, Any], url: str, device_type: str) -> AnalysisResult:
        """解析 API 回應為結構化結果"""
        try:
            # 提取各項評分
            visual = api_response.get('visual_design', {})
            ux = api_response.get('user_experience', {})
            technical = api_response.get('technical_quality', {})
            content = api_response.get('content_quality', {})
            overall = api_response.get('overall', {})
            analysis = api_response.get('analysis', {})
            
            result = AnalysisResult(
                url=url,
                device_type=device_type,
                timestamp=time.time(),
                
                # 視覺設計
                visual_design_score=visual.get('score', 5.0),
                color_scheme_rating=visual.get('color_scheme', 5.0),
                typography_rating=visual.get('typography', 5.0),
                layout_balance_rating=visual.get('layout_balance', 5.0),
                brand_consistency=visual.get('brand_consistency', 5.0),
                
                # 用戶體驗
                ux_score=ux.get('score', 5.0),
                navigation_clarity=ux.get('navigation_clarity', 5.0),
                content_readability=ux.get('content_readability', 5.0),
                cta_effectiveness=ux.get('cta_effectiveness', 5.0),
                mobile_responsiveness=ux.get('mobile_responsiveness', 5.0),
                
                # 技術品質
                technical_score=technical.get('score', 5.0),
                page_structure=technical.get('page_structure', 5.0),
                accessibility_rating=technical.get('accessibility', 5.0),
                performance_impact=technical.get('performance_impact', 5.0),
                
                # 內容品質
                content_score=content.get('score', 5.0),
                content_relevance=content.get('content_relevance', 5.0),
                seo_optimization=content.get('seo_optimization', 5.0),
                multimedia_usage=content.get('multimedia_usage', 5.0),
                
                # 整體
                overall_score=overall.get('score', 5.0),
                analysis_confidence=overall.get('confidence', 0.5),
                
                # 分析內容
                strengths=analysis.get('strengths', []),
                weaknesses=analysis.get('weaknesses', []),
                recommendations=analysis.get('recommendations', []),
                
                # 處理時間
                processing_time=api_response.get('_processing_time', 0)
            )
            
            logger.debug(f"解析分析結果: {url} ({device_type}) = {result.overall_score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"分析結果解析失敗 {url}: {e}")
            # 返回預設結果
            return AnalysisResult(
                url=url,
                device_type=device_type,
                timestamp=time.time(),
                visual_design_score=5.0,
                color_scheme_rating=5.0,
                typography_rating=5.0,
                layout_balance_rating=5.0,
                brand_consistency=5.0,
                ux_score=5.0,
                navigation_clarity=5.0,
                content_readability=5.0,
                cta_effectiveness=5.0,
                mobile_responsiveness=5.0,
                technical_score=5.0,
                page_structure=5.0,
                accessibility_rating=5.0,
                performance_impact=5.0,
                content_score=5.0,
                content_relevance=5.0,
                seo_optimization=5.0,
                multimedia_usage=5.0,
                overall_score=5.0,
                analysis_confidence=0.1,
                strengths=[],
                weaknesses=[],
                recommendations=[],
                processing_time=0,
                error=str(e)
            )
    
    async def analyze_screenshot(self, screenshot_info: ScreenshotInfo) -> AnalysisResult:
        """分析單一截圖"""
        cache_key = f"{screenshot_info.url}_{screenshot_info.device_type}"
        
        # 檢查快取
        if cache_key in self.analysis_cache:
            logger.debug(f"使用快取結果: {cache_key}")
            return self.analysis_cache[cache_key]
        
        if screenshot_info.error:
            logger.warning(f"截圖有錯誤，跳過分析: {screenshot_info.error}")
            return AnalysisResult(
                url=screenshot_info.url,
                device_type=screenshot_info.device_type,
                timestamp=time.time(),
                visual_design_score=0,
                color_scheme_rating=0,
                typography_rating=0,
                layout_balance_rating=0,
                brand_consistency=0,
                ux_score=0,
                navigation_clarity=0,
                content_readability=0,
                cta_effectiveness=0,
                mobile_responsiveness=0,
                technical_score=0,
                page_structure=0,
                accessibility_rating=0,
                performance_impact=0,
                content_score=0,
                content_relevance=0,
                seo_optimization=0,
                multimedia_usage=0,
                overall_score=0,
                analysis_confidence=0,
                strengths=[],
                weaknesses=[],
                recommendations=[],
                processing_time=0,
                error=screenshot_info.error
            )
        
        try:
            logger.info(f"開始分析截圖: {screenshot_info.url} ({screenshot_info.device_type})")
            
            # 優化圖片
            image_base64 = self._optimize_image(screenshot_info.file_path)
            
            # 呼叫 API 分析
            api_response = await self._call_vision_api(
                image_base64, 
                screenshot_info.url, 
                screenshot_info.device_type
            )
            
            # 解析結果
            result = self._parse_api_response(api_response, screenshot_info.url, screenshot_info.device_type)
            
            # 快取結果
            self.analysis_cache[cache_key] = result
            
            logger.info(f"分析完成: {screenshot_info.url} -> 評分 {result.overall_score:.1f}")
            return result
            
        except Exception as e:
            error_msg = f"截圖分析失敗: {e}"
            logger.error(f"{screenshot_info.url} {error_msg}")
            
            return AnalysisResult(
                url=screenshot_info.url,
                device_type=screenshot_info.device_type,
                timestamp=time.time(),
                visual_design_score=0,
                color_scheme_rating=0,
                typography_rating=0,
                layout_balance_rating=0,
                brand_consistency=0,
                ux_score=0,
                navigation_clarity=0,
                content_readability=0,
                cta_effectiveness=0,
                mobile_responsiveness=0,
                technical_score=0,
                page_structure=0,
                accessibility_rating=0,
                performance_impact=0,
                content_score=0,
                content_relevance=0,
                seo_optimization=0,
                multimedia_usage=0,
                overall_score=0,
                analysis_confidence=0,
                strengths=[],
                weaknesses=[],
                recommendations=[],
                processing_time=0,
                error=error_msg
            )
    
    async def analyze_screenshots_batch(self, screenshots: List[ScreenshotInfo], max_concurrent: int = 3) -> List[AnalysisResult]:
        """批量分析截圖"""
        logger.info(f"開始批量分析: {len(screenshots)} 截圖")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(screenshot_info: ScreenshotInfo) -> AnalysisResult:
            async with semaphore:
                return await self.analyze_screenshot(screenshot_info)
        
        # 過濾掉有錯誤的截圖
        valid_screenshots = [s for s in screenshots if not s.error and s.file_path.exists()]
        
        if len(valid_screenshots) != len(screenshots):
            logger.warning(f"跳過 {len(screenshots) - len(valid_screenshots)} 個有錯誤的截圖")
        
        # 並行分析
        tasks = [analyze_with_semaphore(screenshot) for screenshot in valid_screenshots]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        analysis_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量分析異常: {result}")
                # 建立錯誤結果
                screenshot = valid_screenshots[i]
                error_result = AnalysisResult(
                    url=screenshot.url,
                    device_type=screenshot.device_type,
                    timestamp=time.time(),
                    visual_design_score=0,
                    color_scheme_rating=0,
                    typography_rating=0,
                    layout_balance_rating=0,
                    brand_consistency=0,
                    ux_score=0,
                    navigation_clarity=0,
                    content_readability=0,
                    cta_effectiveness=0,
                    mobile_responsiveness=0,
                    technical_score=0,
                    page_structure=0,
                    accessibility_rating=0,
                    performance_impact=0,
                    content_score=0,
                    content_relevance=0,
                    seo_optimization=0,
                    multimedia_usage=0,
                    overall_score=0,
                    analysis_confidence=0,
                    strengths=[],
                    weaknesses=[],
                    recommendations=[],
                    processing_time=0,
                    error=str(result)
                )
                analysis_results.append(error_result)
            else:
                analysis_results.append(result)
        
        successful_analyses = len([r for r in analysis_results if not r.error])
        logger.info(f"批量分析完成: {successful_analyses}/{len(analysis_results)} 成功")
        
        return analysis_results
    
    def calculate_aggregate_scores(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """計算聚合評分和統計"""
        if not results:
            return {}
        
        # 過濾掉有錯誤的結果
        valid_results = [r for r in results if not r.error and r.overall_score > 0]
        
        if not valid_results:
            return {"error": "沒有有效的分析結果"}
        
        # 計算平均分數
        scores = {
            "visual_design": sum(r.visual_design_score for r in valid_results) / len(valid_results),
            "user_experience": sum(r.ux_score for r in valid_results) / len(valid_results),
            "technical_quality": sum(r.technical_score for r in valid_results) / len(valid_results),
            "content_quality": sum(r.content_score for r in valid_results) / len(valid_results),
            "overall": sum(r.overall_score for r in valid_results) / len(valid_results)
        }
        
        # 按設備類型分組
        by_device = {}
        for result in valid_results:
            device = result.device_type
            if device not in by_device:
                by_device[device] = []
            by_device[device].append(result.overall_score)
        
        device_averages = {
            device: sum(scores) / len(scores) 
            for device, scores in by_device.items()
        }
        
        # 收集所有建議
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []
        
        for result in valid_results:
            all_strengths.extend(result.strengths)
            all_weaknesses.extend(result.weaknesses)
            all_recommendations.extend(result.recommendations)
        
        # 統計最常見的問題和建議
        from collections import Counter
        
        return {
            "summary": {
                "total_pages_analyzed": len(valid_results),
                "average_scores": scores,
                "device_scores": device_averages,
                "confidence": sum(r.analysis_confidence for r in valid_results) / len(valid_results)
            },
            "insights": {
                "top_strengths": [item for item, count in Counter(all_strengths).most_common(5)],
                "common_weaknesses": [item for item, count in Counter(all_weaknesses).most_common(5)],
                "priority_recommendations": [item for item, count in Counter(all_recommendations).most_common(10)]
            },
            "statistics": {
                "api_requests": self.request_count,
                "total_tokens": self.total_tokens,
                "cache_hits": len(self.analysis_cache)
            }
        }
    
    def export_results(self, results: List[AnalysisResult], output_path: Path) -> None:
        """匯出分析結果到 JSON 檔案"""
        try:
            export_data = {
                "metadata": {
                    "export_time": time.time(),
                    "total_results": len(results),
                    "analyzer_config": {
                        "service": self.config.service,
                        "model": self.config.model,
                        "max_tokens": self.config.max_tokens
                    }
                },
                "results": [asdict(result) for result in results],
                "aggregates": self.calculate_aggregate_scores(results)
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"分析結果已匯出: {output_path}")
            
        except Exception as e:
            logger.error(f"結果匯出失敗: {e}")
            raise
