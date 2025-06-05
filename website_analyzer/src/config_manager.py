"""
配置管理模組
支援環境變數、YAML 配置檔案和 Azure OpenAI/OpenAI API 切換
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from dataclasses import dataclass
from loguru import logger


@dataclass
class APIConfig:
    """API 配置類"""
    service: str
    model: str
    max_tokens: int
    temperature: float
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None


@dataclass
class BrowserConfig:
    """瀏覽器配置類"""
    headless: bool
    window_size: tuple
    mobile_size: tuple
    tablet_size: tuple
    timeout: int
    wait_time: int


@dataclass
class AnalysisConfig:
    """分析配置類"""
    max_pages: int
    screenshot_formats: list
    batch_size: int
    retry_attempts: int


@dataclass
class OutputConfig:
    """輸出配置類"""
    formats: list
    include_screenshots: bool
    report_title: str


class ConfigManager:
    """配置管理器 - 單例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config = {}
            self._load_config()
            ConfigManager._initialized = True
    
    def _load_config(self):
        """載入配置"""
        # 載入環境變數
        load_dotenv()
        
        # 載入 YAML 配置
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            logger.warning(f"配置檔案不存在: {config_path}")
            self._config = self._get_default_config()
        
        # 環境變數覆蓋配置檔案設定
        self._override_with_env()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """取得預設配置"""
        return {
            "api_service": "azure_openai",
            "azure_openai": {
                "deployment_name": "gpt-4-vision",
                "model": "gpt-4-vision-preview",
                "max_tokens": 2000,
                "temperature": 0.1,
                "api_version": "2024-02-15-preview"
            },
            "openai": {
                "model": "gpt-4-vision-preview",
                "max_tokens": 2000,
                "temperature": 0.1
            },
            "browser": {
                "headless": True,
                "window_size": [1920, 1080],
                "mobile_size": [375, 667],
                "tablet_size": [768, 1024],
                "timeout": 30,
                "wait_time": 5
            },
            "analysis": {
                "max_pages": 50,
                "screenshot_formats": ["desktop", "tablet", "mobile"],
                "batch_size": 5,
                "retry_attempts": 3
            },
            "output": {
                "formats": ["html", "pdf"],
                "include_screenshots": True,
                "report_title": "Website Analysis Report"
            }
        }
    
    def _override_with_env(self):
        """使用環境變數覆蓋配置"""
        env_mappings = {
            "AZURE_OPENAI_API_KEY": ("azure_openai", "api_key"),
            "AZURE_OPENAI_ENDPOINT": ("azure_openai", "endpoint"),
            "AZURE_OPENAI_API_VERSION": ("azure_openai", "api_version"),
            "AZURE_OPENAI_DEPLOYMENT_NAME": ("azure_openai", "deployment_name"),
            "OPENAI_API_KEY": ("openai", "api_key"),
            "BROWSER_HEADLESS": ("browser", "headless"),
            "MAX_PAGES_PER_BATCH": ("analysis", "batch_size"),
            "SCREENSHOT_QUALITY": None,  # 暫時不對應到配置
            "REPORT_OUTPUT_DIR": ("output", "output_dir")
        }
        
        for env_key, config_path in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value and config_path:
                section, key = config_path
                if section not in self._config:
                    self._config[section] = {}
                
                # 類型轉換
                if key == "headless":
                    env_value = env_value.lower() == "true"
                elif key in ["batch_size", "max_pages"]:
                    env_value = int(env_value)
                
                self._config[section][key] = env_value
    
    def get_api_config(self) -> APIConfig:
        """取得 API 配置"""
        service = self._config.get("api_service", "azure_openai")
        
        if service == "azure_openai":
            azure_config = self._config.get("azure_openai", {})
            return APIConfig(
                service="azure_openai",
                model=azure_config.get("model", "gpt-4-vision-preview"),
                max_tokens=azure_config.get("max_tokens", 2000),
                temperature=azure_config.get("temperature", 0.1),
                api_key=os.getenv("AZURE_OPENAI_API_KEY") or azure_config.get("api_key"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") or azure_config.get("endpoint"),
                api_version=azure_config.get("api_version", "2024-02-15-preview"),
                deployment_name=azure_config.get("deployment_name", "gpt-4-vision")
            )
        else:
            openai_config = self._config.get("openai", {})
            return APIConfig(
                service="openai",
                model=openai_config.get("model", "gpt-4-vision-preview"),
                max_tokens=openai_config.get("max_tokens", 2000),
                temperature=openai_config.get("temperature", 0.1),
                api_key=os.getenv("OPENAI_API_KEY") or openai_config.get("api_key")
            )
    
    def get_browser_config(self) -> BrowserConfig:
        """取得瀏覽器配置"""
        browser_config = self._config.get("browser", {})
        return BrowserConfig(
            headless=browser_config.get("headless", True),
            window_size=tuple(browser_config.get("window_size", [1920, 1080])),
            mobile_size=tuple(browser_config.get("mobile_size", [375, 667])),
            tablet_size=tuple(browser_config.get("tablet_size", [768, 1024])),
            timeout=browser_config.get("timeout", 30),
            wait_time=browser_config.get("wait_time", 5)
        )
    
    def get_analysis_config(self) -> AnalysisConfig:
        """取得分析配置"""
        analysis_config = self._config.get("analysis", {})
        return AnalysisConfig(
            max_pages=analysis_config.get("max_pages", 50),
            screenshot_formats=analysis_config.get("screenshot_formats", ["desktop", "tablet", "mobile"]),
            batch_size=analysis_config.get("batch_size", 5),
            retry_attempts=analysis_config.get("retry_attempts", 3)
        )
    
    def get_output_config(self) -> OutputConfig:
        """取得輸出配置"""
        output_config = self._config.get("output", {})
        return OutputConfig(
            formats=output_config.get("formats", ["html", "pdf"]),
            include_screenshots=output_config.get("include_screenshots", True),
            report_title=output_config.get("report_title", "Website Analysis Report")
        )
    
    def get_output_dir(self) -> Path:
        """取得輸出目錄"""
        output_dir = os.getenv("REPORT_OUTPUT_DIR", "./reports")
        return Path(output_dir)
    
    def validate_config(self) -> bool:
        """驗證配置"""
        api_config = self.get_api_config()
        
        if not api_config.api_key:
            logger.error(f"API key 未設定 for {api_config.service}")
            return False
        
        if api_config.service == "azure_openai" and not api_config.endpoint:
            logger.error("Azure OpenAI endpoint 未設定")
            return False
        
        logger.info(f"配置驗證成功 - API 服務: {api_config.service}")
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """取得配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


# 全域配置管理器實例
config_manager = ConfigManager()
