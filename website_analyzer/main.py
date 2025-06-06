#!/usr/bin/env python3
"""
Website Analyzer - Main Entry Point
Automated website analysis system with sitemap parsing, browser automation, and GPT vision analysis.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from src.config_manager import config_manager
from src.sitemap_parser import SitemapParser
from src.browser_automation import BrowserAutomation
from src.gpt_analyzer import GPTAnalyzer
from src.report_generator import ReportGenerator
from src.logging_utils import get_logger, setup_root_logger


class WebsiteAnalyzer:
    """Main orchestrator for the website analysis system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the website analyzer."""
        # ConfigManager is a singleton, configuration path is currently ignored
        self.config_manager = config_manager

        # Core components
        self.sitemap_parser = SitemapParser()
        self.browser_automation = BrowserAutomation()
        self.gpt_analyzer = GPTAnalyzer()
        self.report_generator = ReportGenerator()

        # Setup enhanced logging with default configuration
        self._setup_logging()
        self.logger = get_logger(__name__)
        
    def _setup_logging(self):
        """Setup logging configuration."""
        # Use default logging configuration from logging_utils
        setup_root_logger({})
        
    async def analyze_website(
        self,
        url: str,
        max_pages: Optional[int] = None,
        output_dir: Optional[str] = None,
        report_format: str = "html"
    ) -> Dict[str, Any]:
        """
        Perform complete website analysis.
        
        Args:
            url: Base URL of the website to analyze
            max_pages: Maximum number of pages to analyze
            output_dir: Output directory for reports
            report_format: Report format (html, pdf, json)
            
        Returns:
            Analysis results dictionary
        """
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.analysis_start(url, analysis_id)
        start_time = datetime.now()
        
        try:
            # Step 1: Parse sitemap and discover URLs
            self.logger.logger.info("Step 1: Parsing sitemap and discovering URLs")
            async with SitemapParser() as parser:
                url_infos = await parser.parse_website(url)
            urls = [u.url for u in url_infos]

            if max_pages:
                urls = urls[:max_pages]

            self.logger.logger.info(f"Found {len(urls)} URLs to analyze")

            # Step 2: Browser automation - capture screenshots and collect data
            self.logger.logger.info("Step 2: Capturing screenshots and collecting browser data")
            async with BrowserAutomation() as browser:
                browser_results = await browser.analyze_pages_comprehensive(urls)

            screenshots = browser_results.get("screenshots", [])

            # Step 3: GPT Vision Analysis
            self.logger.logger.info("Step 3: Performing GPT vision analysis")
            async with GPTAnalyzer() as analyzer:
                analysis_results = await analyzer.analyze_screenshots_batch(screenshots)

            # Step 4: Generate comprehensive report
            self.logger.logger.info("Step 4: Generating analysis report")
            if not output_dir:
                output_dir = f"reports/{self._sanitize_url(url)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            reports = self.report_generator.generate_comprehensive_report(
                analysis_results,
                screenshots,
                browser_results.get("performance_metrics"),
                browser_results.get("interaction_results"),
                formats=[report_format]
            )
            report_path = reports.get(report_format)
            
            # Compile final results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results = {
                'website_url': url,
                'analysis_date': start_time.isoformat(),
                'duration_seconds': duration,
                'pages_analyzed': len(urls),
                'report_path': str(report_path),
                'summary': self._generate_summary(analysis_results),
                'detailed_results': analysis_results
            }
            
            self.logger.analysis_complete(url, analysis_id, duration, len(urls))
            self.logger.performance_metric("analysis_duration", duration)
            self.logger.performance_metric("pages_per_second", len(urls) / duration if duration > 0 else 0, "pages/sec")
            
            return results
            
        except Exception as e:
            self.logger.error_occurred(e, {
                'url': url,
                'analysis_id': analysis_id,
                'max_pages': max_pages,
                'output_dir': output_dir,
                'report_format': report_format
            })
            raise
            
    async def analyze_multiple_websites(
        self,
        urls: List[str],
        max_pages_per_site: Optional[int] = None,
        output_dir: Optional[str] = None,
        report_format: str = "html"
    ) -> Dict[str, Any]:
        """
        Analyze multiple websites in batch.
        
        Args:
            urls: List of website URLs to analyze
            max_pages_per_site: Maximum pages per website
            output_dir: Output directory for reports
            report_format: Report format
            
        Returns:
            Batch analysis results
        """
        self.logger.info(f"Starting batch analysis for {len(urls)} websites")
        
        results = {}
        errors = {}
        
        for url in urls:
            try:
                self.logger.info(f"Analyzing website: {url}")
                result = await self.analyze_website(
                    url, max_pages_per_site, output_dir, report_format
                )
                results[url] = result
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {url}: {str(e)}")
                errors[url] = str(e)
                
        return {
            'successful': results,
            'failed': errors,
            'total_websites': len(urls),
            'successful_count': len(results),
            'failed_count': len(errors)
        }
        
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL for use in file names."""
        return url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
        
    def _generate_summary(self, analysis_results: List[Any]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        if not analysis_results:
            return {}

        analyzer = GPTAnalyzer()
        aggregates = analyzer.calculate_aggregate_scores(analysis_results)
        return aggregates.get('summary', {})
        
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade based on average score."""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Website Analyzer - Automated website analysis with GPT vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py analyze https://example.com
  python main.py analyze https://example.com --max-pages 10 --format pdf
  python main.py batch-analyze urls.txt --output-dir ./reports
  python main.py analyze https://example.com --config custom_config.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single website analysis
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single website')
    analyze_parser.add_argument('url', help='Website URL to analyze')
    analyze_parser.add_argument('--max-pages', type=int, help='Maximum number of pages to analyze')
    analyze_parser.add_argument('--output-dir', help='Output directory for reports')
    analyze_parser.add_argument('--format', choices=['html', 'pdf', 'json'], default='html',
                               help='Report format (default: html)')
    analyze_parser.add_argument('--config', help='Configuration file path')
    
    # Batch analysis
    batch_parser = subparsers.add_parser('batch-analyze', help='Analyze multiple websites')
    batch_parser.add_argument('urls_file', help='File containing URLs (one per line)')
    batch_parser.add_argument('--max-pages', type=int, help='Maximum pages per website')
    batch_parser.add_argument('--output-dir', help='Output directory for reports')
    batch_parser.add_argument('--format', choices=['html', 'pdf', 'json'], default='html',
                             help='Report format (default: html)')
    batch_parser.add_argument('--config', help='Configuration file path')
    
    # Configuration validation
    config_parser = subparsers.add_parser('validate-config', help='Validate configuration')
    config_parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    try:
        if args.command == 'analyze':
            analyzer = WebsiteAnalyzer(getattr(args, 'config', None))
            results = await analyzer.analyze_website(
                args.url,
                args.max_pages,
                args.output_dir,
                args.format
            )
            
            print("\n" + "="*60)
            print("ANALYSIS COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"Website: {results['website_url']}")
            print(f"Pages analyzed: {results['pages_analyzed']}")
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            print(f"Report: {results['report_path']}")
            print(f"Overall Grade: {results['summary'].get('performance_grade', 'N/A')}")
            print("="*60)
            
        elif args.command == 'batch-analyze':
            # Read URLs from file
            urls_file = Path(args.urls_file)
            if not urls_file.exists():
                print(f"Error: URLs file not found: {urls_file}")
                return
                
            urls = []
            with open(urls_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        urls.append(url)
                        
            if not urls:
                print("Error: No valid URLs found in file")
                return
                
            analyzer = WebsiteAnalyzer(getattr(args, 'config', None))
            results = await analyzer.analyze_multiple_websites(
                urls,
                args.max_pages,
                args.output_dir,
                args.format
            )
            
            print("\n" + "="*60)
            print("BATCH ANALYSIS COMPLETED")
            print("="*60)
            print(f"Total websites: {results['total_websites']}")
            print(f"Successful: {results['successful_count']}")
            print(f"Failed: {results['failed_count']}")
            print("="*60)
            
        elif args.command == 'validate-config':
            if config_manager.validate_config():
                print("✓ Configuration is valid")
            else:
                print("✗ Configuration validation failed")
                
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
