"""
報告生成模組
整合分析結果，生成可視化報告，支援 HTML 和 PDF 格式
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import base64

# 報告生成依賴
from jinja2 import Environment, FileSystemLoader, Template
try:
    import weasyprint
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("警告: weasyprint 未安裝，PDF 生成功能不可用")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 非互動模式
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: matplotlib 未安裝，圖表生成功能不可用")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.offline import plot
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("警告: plotly 未安裝，互動圖表功能不可用")

from loguru import logger

from .config_manager import config_manager
from .gpt_analyzer import AnalysisResult
from .browser_automation import ScreenshotInfo, PageMetrics, InteractionResult


class ReportGenerator:
    """報告生成器"""
    
    def __init__(self, output_dir: Path = None):
        self.output_config = config_manager.get_output_config()
        self.output_dir = output_dir or config_manager.get_output_dir()
        self.output_dir.mkdir(exist_ok=True)
        
        # 建立模板環境
        self.template_env = self._setup_template_environment()
        
        # 圖表輸出目錄
        self.charts_dir = self.output_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True)
        
        # 靜態資源目錄
        self.assets_dir = self.output_dir / "assets"
        self.assets_dir.mkdir(exist_ok=True)
    
    def _setup_template_environment(self) -> Environment:
        """設置模板環境"""
        # 設置模板目錄
        template_dir = Path(__file__).parent.parent / "templates"
        
        # 如果模板目錄不存在，建立並使用內建模板
        if not template_dir.exists():
            template_dir.mkdir(exist_ok=True)
            self._create_default_templates(template_dir)
        
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        # 添加自訂過濾器
        env.filters['datetime'] = self._format_datetime
        env.filters['score_color'] = self._get_score_color
        env.filters['score_grade'] = self._get_score_grade
        env.filters['base64_image'] = self._encode_image_base64
        
        return env
    
    def _create_default_templates(self, template_dir: Path):
        """建立預設模板"""
        # 建立 HTML 報告模板
        html_template = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 40px;
        }
        .section {
            margin-bottom: 40px;
            padding: 30px;
            background: #fafafa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            color: #333;
            margin-top: 0;
            font-size: 1.8em;
            font-weight: 500;
        }
        .score-card {
            display: inline-block;
            padding: 20px;
            margin: 10px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 150px;
        }
        .score-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .score-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .grade-a { color: #4CAF50; }
        .grade-b { color: #8BC34A; }
        .grade-c { color: #FFC107; }
        .grade-d { color: #FF9800; }
        .grade-f { color: #F44336; }
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .screenshot-item {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .screenshot-item img {
            width: 100%;
            height: auto;
            display: block;
        }
        .screenshot-info {
            padding: 15px;
        }
        .device-label {
            display: inline-block;
            padding: 4px 8px;
            background: #667eea;
            color: white;
            border-radius: 4px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }
        .insights {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .insight-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .insight-box h3 {
            margin-top: 0;
            color: #333;
        }
        .insight-list {
            list-style: none;
            padding: 0;
        }
        .insight-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .insight-list li:last-child {
            border-bottom: none;
        }
        .positive { color: #4CAF50; }
        .negative { color: #F44336; }
        .neutral { color: #2196F3; }
        .footer {
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        @media print {
            body { background: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <div class="subtitle">
                網站分析報告 • {{ analysis_date | datetime }}
            </div>
        </div>
        
        <div class="content">
            <!-- 執行摘要 -->
            <div class="section">
                <h2>📊 執行摘要</h2>
                <div class="score-cards">
                    <div class="score-card">
                        <div class="score-label">整體評分</div>
                        <div class="score-value {{ summary.average_scores.overall | score_color }}">
                            {{ "%.1f" | format(summary.average_scores.overall) }}
                        </div>
                        <div class="score-grade">{{ summary.average_scores.overall | score_grade }}</div>
                    </div>
                    <div class="score-card">
                        <div class="score-label">視覺設計</div>
                        <div class="score-value {{ summary.average_scores.visual_design | score_color }}">
                            {{ "%.1f" | format(summary.average_scores.visual_design) }}
                        </div>
                    </div>
                    <div class="score-card">
                        <div class="score-label">用戶體驗</div>
                        <div class="score-value {{ summary.average_scores.user_experience | score_color }}">
                            {{ "%.1f" | format(summary.average_scores.user_experience) }}
                        </div>
                    </div>
                    <div class="score-card">
                        <div class="score-label">技術品質</div>
                        <div class="score-value {{ summary.average_scores.technical_quality | score_color }}">
                            {{ "%.1f" | format(summary.average_scores.technical_quality) }}
                        </div>
                    </div>
                    <div class="score-card">
                        <div class="score-label">內容品質</div>
                        <div class="score-value {{ summary.average_scores.content_quality | score_color }}">
                            {{ "%.1f" | format(summary.average_scores.content_quality) }}
                        </div>
                    </div>
                </div>
                
                <p><strong>分析了 {{ summary.total_pages_analyzed }} 個頁面</strong>，
                平均評分為 <strong>{{ "%.1f" | format(summary.average_scores.overall) }}</strong>。
                分析信心度: {{ "%.0f" | format(summary.confidence * 100) }}%</p>
            </div>
            
            <!-- 關鍵發現 -->
            <div class="section">
                <h2>🔍 關鍵發現</h2>
                <div class="insights">
                    <div class="insight-box">
                        <h3 class="positive">✅ 主要優勢</h3>
                        <ul class="insight-list">
                            {% for strength in insights.top_strengths %}
                            <li>{{ strength }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    <div class="insight-box">
                        <h3 class="negative">⚠️ 需要改進</h3>
                        <ul class="insight-list">
                            {% for weakness in insights.common_weaknesses %}
                            <li>{{ weakness }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 優化建議 -->
            <div class="section">
                <h2>💡 優化建議</h2>
                <div class="insight-box">
                    <ul class="insight-list">
                        {% for recommendation in insights.priority_recommendations %}
                        <li class="neutral">{{ recommendation }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <!-- 頁面詳細分析 -->
            {% if page_details %}
            <div class="section">
                <h2>📱 頁面詳細分析</h2>
                {% for page in page_details %}
                <div style="margin-bottom: 30px; padding: 20px; background: white; border-radius: 8px;">
                    <h3>{{ page.url }}</h3>
                    <p><strong>整體評分:</strong> 
                        <span class="{{ page.overall_score | score_color }}">{{ "%.1f" | format(page.overall_score) }}</span>
                        ({{ page.overall_score | score_grade }})
                    </p>
                    
                    {% if page.screenshots %}
                    <div class="screenshot-grid">
                        {% for screenshot in page.screenshots %}
                        <div class="screenshot-item">
                            {% if screenshot.file_path.exists() %}
                            <img src="data:image/png;base64,{{ screenshot.file_path | base64_image }}" 
                                 alt="Screenshot of {{ page.url }}">
                            {% endif %}
                            <div class="screenshot-info">
                                <div class="device-label">{{ screenshot.device_type }}</div>
                                <div>載入時間: {{ "%.2f" | format(screenshot.load_time) }}s</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- 統計資訊 -->
            <div class="section">
                <h2>📈 分析統計</h2>
                <div class="insights">
                    <div class="insight-box">
                        <h3>API 使用統計</h3>
                        <p>API 請求次數: {{ statistics.api_requests }}</p>
                        <p>消耗 Token 數: {{ statistics.total_tokens }}</p>
                        <p>快取命中: {{ statistics.cache_hits }}</p>
                    </div>
                    <div class="insight-box">
                        <h3>設備評分對比</h3>
                        {% for device, score in summary.device_scores.items() %}
                        <p>{{ device|title }}: <span class="{{ score | score_color }}">{{ "%.1f" | format(score) }}</span></p>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>報告生成時間: {{ analysis_date | datetime }} | 
               使用 Website Analyzer v1.0 生成</p>
        </div>
    </div>
</body>
</html>
'''
        
        # 儲存模板
        with open(template_dir / "report_template.html", "w", encoding="utf-8") as f:
            f.write(html_template)
        
        logger.info(f"已建立預設模板: {template_dir}")
    
    def _format_datetime(self, timestamp: float) -> str:
        """格式化時間戳"""
        return datetime.fromtimestamp(timestamp).strftime("%Y年%m月%d日 %H:%M")
    
    def _get_score_color(self, score: float) -> str:
        """根據評分取得顏色類別"""
        if score >= 8.0:
            return "grade-a"
        elif score >= 6.0:
            return "grade-b"
        elif score >= 4.0:
            return "grade-c"
        elif score >= 2.0:
            return "grade-d"
        else:
            return "grade-f"
    
    def _get_score_grade(self, score: float) -> str:
        """根據評分取得等級"""
        if score >= 8.0:
            return "優秀"
        elif score >= 6.0:
            return "良好"
        elif score >= 4.0:
            return "普通"
        elif score >= 2.0:
            return "待改進"
        else:
            return "需要重大改進"
    
    def _encode_image_base64(self, image_path: Path) -> str:
        """將圖片編碼為 base64"""
        try:
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            if image_path.exists():
                with open(image_path, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"圖片編碼失敗 {image_path}: {e}")
            return ""
    
    def _create_score_charts(self, analysis_results: List[AnalysisResult]) -> Dict[str, Path]:
        """建立評分圖表"""
        chart_files = {}
        
        if not MATPLOTLIB_AVAILABLE and not PLOTLY_AVAILABLE:
            logger.warning("圖表庫不可用，跳過圖表生成")
            return chart_files
        
        try:
            # 準備資料
            urls = [r.url for r in analysis_results if not r.error]
            visual_scores = [r.visual_design_score for r in analysis_results if not r.error]
            ux_scores = [r.ux_score for r in analysis_results if not r.error]
            technical_scores = [r.technical_score for r in analysis_results if not r.error]
            content_scores = [r.content_score for r in analysis_results if not r.error]
            overall_scores = [r.overall_score for r in analysis_results if not r.error]
            
            if not urls:
                return chart_files
            
            # 使用 Plotly 建立互動圖表 (優先)
            if PLOTLY_AVAILABLE:
                # 雷達圖 - 平均分數
                avg_scores = {
                    '視覺設計': sum(visual_scores) / len(visual_scores),
                    '用戶體驗': sum(ux_scores) / len(ux_scores),
                    '技術品質': sum(technical_scores) / len(technical_scores),
                    '內容品質': sum(content_scores) / len(content_scores)
                }
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(avg_scores.values()),
                    theta=list(avg_scores.keys()),
                    fill='toself',
                    name='平均評分'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )),
                    showlegend=True,
                    title="各維度平均評分",
                    font=dict(family="Microsoft JhengHei, Arial", size=12)
                )
                
                radar_path = self.charts_dir / "radar_chart.html"
                fig_radar.write_html(str(radar_path))
                chart_files['radar'] = radar_path
                
                # 整體評分趨勢圖
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Bar(
                    x=[f"頁面 {i+1}" for i in range(len(overall_scores))],
                    y=overall_scores,
                    name='整體評分',
                    marker_color='rgba(102, 126, 234, 0.8)'
                ))
                fig_trend.update_layout(
                    title="各頁面整體評分",
                    xaxis_title="頁面",
                    yaxis_title="評分",
                    yaxis=dict(range=[0, 10]),
                    font=dict(family="Microsoft JhengHei, Arial", size=12)
                )
                
                trend_path = self.charts_dir / "trend_chart.html"
                fig_trend.write_html(str(trend_path))
                chart_files['trend'] = trend_path
            
            # 使用 Matplotlib 建立靜態圖表 (備用)
            elif MATPLOTLIB_AVAILABLE:
                plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 建立評分對比圖
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
                
                # 各維度平均分數柱狀圖
                categories = ['視覺設計', '用戶體驗', '技術品質', '內容品質']
                avg_scores = [
                    sum(visual_scores) / len(visual_scores),
                    sum(ux_scores) / len(ux_scores),
                    sum(technical_scores) / len(technical_scores),
                    sum(content_scores) / len(content_scores)
                ]
                
                bars = ax1.bar(categories, avg_scores, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
                ax1.set_title('各維度平均評分', fontsize=16, fontweight='bold')
                ax1.set_ylabel('評分', fontsize=12)
                ax1.set_ylim(0, 10)
                
                # 在柱子上顯示數值
                for bar, score in zip(bars, avg_scores):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{score:.1f}', ha='center', va='bottom', fontsize=11)
                
                # 整體評分趨勢圖
                x_labels = [f'頁面{i+1}' for i in range(len(overall_scores))]
                ax2.plot(x_labels, overall_scores, marker='o', linewidth=2, markersize=6, color='#667eea')
                ax2.set_title('各頁面整體評分趨勢', fontsize=16, fontweight='bold')
                ax2.set_ylabel('評分', fontsize=12)
                ax2.set_ylim(0, 10)
                ax2.grid(True, alpha=0.3)
                
                # 旋轉 x 軸標籤以避免重疊
                if len(x_labels) > 10:
                    ax2.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                
                chart_path = self.charts_dir / "scores_chart.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                chart_files['scores'] = chart_path
            
            logger.info(f"圖表生成完成: {list(chart_files.keys())}")
            
        except Exception as e:
            logger.error(f"圖表生成失敗: {e}")
        
        return chart_files
    
    def _prepare_report_data(self, analysis_results: List[AnalysisResult], 
                           screenshots: List[ScreenshotInfo] = None,
                           performance_metrics: List[PageMetrics] = None,
                           interaction_results: List[InteractionResult] = None) -> Dict[str, Any]:
        """準備報告資料"""
        
        # 計算聚合評分
        from .gpt_analyzer import GPTAnalyzer
        analyzer = GPTAnalyzer()
        aggregates = analyzer.calculate_aggregate_scores(analysis_results)
        
        # 準備頁面詳細資料
        page_details = []
        url_to_screenshots = {}
        
        if screenshots:
            for screenshot in screenshots:
                if screenshot.url not in url_to_screenshots:
                    url_to_screenshots[screenshot.url] = []
                url_to_screenshots[screenshot.url].append(screenshot)
        
        # 按 URL 分組分析結果
        url_to_results = {}
        for result in analysis_results:
            if result.url not in url_to_results:
                url_to_results[result.url] = []
            url_to_results[result.url].append(result)
        
        for url, results in url_to_results.items():
            # 計算該 URL 的平均評分
            valid_results = [r for r in results if not r.error]
            if valid_results:
                avg_score = sum(r.overall_score for r in valid_results) / len(valid_results)
                page_detail = {
                    'url': url,
                    'overall_score': avg_score,
                    'results': valid_results,
                    'screenshots': url_to_screenshots.get(url, [])
                }
                page_details.append(page_detail)
        
        # 按評分排序
        page_details.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return {
            'report_title': self.output_config.report_title,
            'analysis_date': time.time(),
            'summary': aggregates.get('summary', {}),
            'insights': aggregates.get('insights', {}),
            'statistics': aggregates.get('statistics', {}),
            'page_details': page_details[:10],  # 只顯示前 10 個頁面
            'total_results': len(analysis_results),
            'successful_results': len([r for r in analysis_results if not r.error])
        }
    
    def generate_html_report(self, analysis_results: List[AnalysisResult],
                           screenshots: List[ScreenshotInfo] = None,
                           performance_metrics: List[PageMetrics] = None,
                           interaction_results: List[InteractionResult] = None,
                           output_filename: str = None) -> Path:
        """生成 HTML 報告"""
        try:
            # 準備報告資料
            report_data = self._prepare_report_data(
                analysis_results, screenshots, performance_metrics, interaction_results
            )
            
            # 生成圖表
            charts = self._create_score_charts(analysis_results)
            report_data['charts'] = charts
            
            # 載入模板
            template = self.template_env.get_template('report_template.html')
            
            # 渲染 HTML
            html_content = template.render(**report_data)
            
            # 輸出檔案
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"website_analysis_report_{timestamp}.html"
            
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML 報告已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"HTML 報告生成失敗: {e}")
            raise
    
    def generate_pdf_report(self, analysis_results: List[AnalysisResult],
                          screenshots: List[ScreenshotInfo] = None,
                          performance_metrics: List[PageMetrics] = None,
                          interaction_results: List[InteractionResult] = None,
                          output_filename: str = None) -> Optional[Path]:
        """生成 PDF 報告"""
        if not WEASYPRINT_AVAILABLE:
            logger.warning("weasyprint 不可用，跳過 PDF 生成")
            return None
        
        try:
            # 先生成 HTML 報告
            html_path = self.generate_html_report(
                analysis_results, screenshots, performance_metrics, interaction_results,
                output_filename="temp_report_for_pdf.html"
            )
            
            # 轉換為 PDF
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"website_analysis_report_{timestamp}.pdf"
            
            pdf_path = self.output_dir / output_filename
            
            # 使用 weasyprint 轉換
            HTML(str(html_path)).write_pdf(str(pdf_path))
            
            # 清理臨時 HTML 檔案
            html_path.unlink()
            
            logger.info(f"PDF 報告已生成: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"PDF 報告生成失敗: {e}")
            return None
    
    def generate_json_report(self, analysis_results: List[AnalysisResult],
                           screenshots: List[ScreenshotInfo] = None,
                           performance_metrics: List[PageMetrics] = None,
                           interaction_results: List[InteractionResult] = None,
                           output_filename: str = None) -> Path:
        """生成 JSON 格式報告"""
        try:
            # 準備完整資料
            report_data = {
                'metadata': {
                    'report_title': self.output_config.report_title,
                    'generation_time': time.time(),
                    'generator_version': '1.0'
                },
                'analysis_results': [asdict(result) for result in analysis_results],
                'screenshots': [asdict(screenshot) for screenshot in screenshots] if screenshots else [],
                'performance_metrics': [asdict(metric) for metric in performance_metrics] if performance_metrics else [],
                'interaction_results': [asdict(result) for result in interaction_results] if interaction_results else []
            }
            
            # 計算聚合資料
            from .gpt_analyzer import GPTAnalyzer
            analyzer = GPTAnalyzer()
            aggregates = analyzer.calculate_aggregate_scores(analysis_results)
            report_data['aggregates'] = aggregates
            
            # 輸出檔案
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"website_analysis_data_{timestamp}.json"
            
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"JSON 報告已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"JSON 報告生成失敗: {e}")
            raise
    
    def generate_comprehensive_report(self, analysis_results: List[AnalysisResult],
                                    screenshots: List[ScreenshotInfo] = None,
                                    performance_metrics: List[PageMetrics] = None,
                                    interaction_results: List[InteractionResult] = None,
                                    formats: List[str] = None) -> Dict[str, Path]:
        """生成完整報告 (多種格式)"""
        if formats is None:
            formats = self.output_config.formats
        
        generated_reports = {}
        
        try:
            # 生成 HTML 報告
            if 'html' in formats:
                html_path = self.generate_html_report(
                    analysis_results, screenshots, performance_metrics, interaction_results
                )
                generated_reports['html'] = html_path
            
            # 生成 PDF 報告
            if 'pdf' in formats and WEASYPRINT_AVAILABLE:
                pdf_path = self.generate_pdf_report(
                    analysis_results, screenshots, performance_metrics, interaction_results
                )
                if pdf_path:
                    generated_reports['pdf'] = pdf_path
            
            # 生成 JSON 報告
            if 'json' in formats:
                json_path = self.generate_json_report(
                    analysis_results, screenshots, performance_metrics, interaction_results
                )
                generated_reports['json'] = json_path
            
            logger.info(f"報告生成完成: {list(generated_reports.keys())}")
            return generated_reports
            
        except Exception as e:
            logger.error(f"完整報告生成失敗: {e}")
            raise
    
    def create_summary_dashboard(self, analysis_results: List[AnalysisResult]) -> Optional[Path]:
        """建立摘要儀表板 (使用 Plotly)"""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly 不可用，跳過儀表板生成")
            return None
        
        try:
            from plotly.subplots import make_subplots
            
            # 準備資料
            valid_results = [r for r in analysis_results if not r.error]
            if not valid_results:
                return None
            
            # 建立子圖
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('各維度平均評分', '設備類型對比', '評分分布', '頁面評分排名'),
                specs=[[{"type": "bar"}, {"type": "bar"}],
                       [{"type": "histogram"}, {"type": "bar"}]]
            )
            
            # 1. 各維度平均評分
            categories = ['視覺設計', '用戶體驗', '技術品質', '內容品質']
            avg_scores = [
                sum(r.visual_design_score for r in valid_results) / len(valid_results),
                sum(r.ux_score for r in valid_results) / len(valid_results),
                sum(r.technical_score for r in valid_results) / len(valid_results),
                sum(r.content_score for r in valid_results) / len(valid_results)
            ]
            
            fig.add_trace(
                go.Bar(x=categories, y=avg_scores, name='平均評分',
                      marker_color='rgba(102, 126, 234, 0.8)'),
                row=1, col=1
            )
            
            # 2. 設備類型對比
            device_scores = {}
            for result in valid_results:
                device = result.device_type
                if device not in device_scores:
                    device_scores[device] = []
                device_scores[device].append(result.overall_score)
            
            device_avg = {device: sum(scores)/len(scores) for device, scores in device_scores.items()}
            
            fig.add_trace(
                go.Bar(x=list(device_avg.keys()), y=list(device_avg.values()),
                      name='設備評分', marker_color='rgba(255, 107, 107, 0.8)'),
                row=1, col=2
            )
            
            # 3. 評分分布直方圖
            overall_scores = [r.overall_score for r in valid_results]
            fig.add_trace(
                go.Histogram(x=overall_scores, nbinsx=20, name='評分分布',
                           marker_color='rgba(78, 205, 196, 0.8)'),
                row=2, col=1
            )
            
            # 4. 頁面評分排名 (前10)
            url_scores = {}
            for result in valid_results:
                if result.url not in url_scores:
                    url_scores[result.url] = []
                url_scores[result.url].append(result.overall_score)
            
            url_avg = {url: sum(scores)/len(scores) for url, scores in url_scores.items()}
            top_urls = sorted(url_avg.items(), key=lambda x: x[1], reverse=True)[:10]
            
            fig.add_trace(
                go.Bar(
                    x=[f"頁面{i+1}" for i in range(len(top_urls))],
                    y=[score for _, score in top_urls],
                    name='頁面排名',
                    marker_color='rgba(150, 206, 180, 0.8)',
                    text=[url.split('/')[-1][:20] for url, _ in top_urls],
                    textposition='outside'
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="網站分析儀表板",
                showlegend=False,
                font=dict(family="Microsoft JhengHei, Arial", size=12)
            )
            
            # 儲存儀表板
            dashboard_path = self.charts_dir / "analysis_dashboard.html"
            fig.write_html(str(dashboard_path))
            
            logger.info(f"分析儀表板已生成: {dashboard_path}")
            return dashboard_path
            
        except Exception as e:
            logger.error(f"儀表板生成失敗: {e}")
            return None
