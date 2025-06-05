#!/usr/bin/env python3
"""
Example script demonstrating programmatic usage of the Website Analyzer.
This script shows various ways to use the analyzer components individually or together.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from src.config_manager import ConfigManager
from src.sitemap_parser import SitemapParser
from src.browser_automation import BrowserAutomation
from src.gpt_analyzer import GPTAnalyzer
from src.report_generator import ReportGenerator
from main import WebsiteAnalyzer


async def example_single_site_analysis():
    """Example: Analyze a single website with custom configuration."""
    
    print("🔍 Example 1: Single Website Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = WebsiteAnalyzer()
    
    # Analyze website
    results = await analyzer.analyze_website(
        url="https://example.com",
        max_pages=5,
        output_dir="examples/reports/single_site",
        report_format="html"
    )
    
    print(f"✅ Analysis completed!")
    print(f"   📊 Pages analyzed: {results['pages_analyzed']}")
    print(f"   ⏱️  Duration: {results['duration_seconds']:.2f} seconds")
    print(f"   📁 Report: {results['report_path']}")
    print(f"   🎯 Grade: {results['summary'].get('performance_grade', 'N/A')}")
    print()


async def example_batch_analysis():
    """Example: Batch analysis of multiple websites."""
    
    print("🔍 Example 2: Batch Website Analysis")
    print("=" * 50)
    
    # List of websites to analyze
    websites = [
        "https://example.com",
        "https://httpbin.org",
        "https://jsonplaceholder.typicode.com"
    ]
    
    analyzer = WebsiteAnalyzer()
    
    # Run batch analysis
    results = await analyzer.analyze_multiple_websites(
        urls=websites,
        max_pages_per_site=3,
        output_dir="examples/reports/batch_analysis",
        report_format="html"
    )
    
    print(f"✅ Batch analysis completed!")
    print(f"   🌐 Total websites: {results['total_websites']}")
    print(f"   ✅ Successful: {results['successful_count']}")
    print(f"   ❌ Failed: {results['failed_count']}")
    print()


async def example_component_usage():
    """Example: Using individual components."""
    
    print("🔍 Example 3: Individual Component Usage")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = ConfigManager()
    
    # 1. Sitemap parsing
    print("📋 Step 1: Parsing sitemap...")
    sitemap_parser = SitemapParser(config_manager)
    urls = await sitemap_parser.parse_sitemap("https://example.com")
    print(f"   Found {len(urls)} URLs")
    
    # Limit to first 2 URLs for example
    urls = urls[:2]
    
    # 2. Browser automation
    print("🌐 Step 2: Browser automation...")
    browser_automation = BrowserAutomation(config_manager)
    browser_results = await browser_automation.process_urls(urls)
    print(f"   Captured {len(browser_results)} page screenshots")
    
    # 3. GPT analysis
    print("🤖 Step 3: GPT analysis...")
    gpt_analyzer = GPTAnalyzer(config_manager)
    analysis_results = await gpt_analyzer.analyze_batch(browser_results)
    print(f"   Analyzed {len(analysis_results)} pages")
    
    # 4. Report generation
    print("📊 Step 4: Report generation...")
    report_generator = ReportGenerator(config_manager)
    report_path = await report_generator.generate_report(
        analysis_results,
        "examples/reports/component_usage",
        "html"
    )
    print(f"   Report generated: {report_path}")
    print()


async def example_custom_configuration():
    """Example: Using custom configuration."""
    
    print("🔍 Example 4: Custom Configuration")
    print("=" * 50)
    
    # Create custom config
    custom_config = {
        'api': {
            'service': 'openai',
            'openai': {
                'model': 'gpt-4-vision-preview',
                'max_tokens': 2000,
                'temperature': 0.2
            }
        },
        'browser': {
            'headless': True,
            'timeout': 20,
            'viewports': {
                'desktop': {'width': 1366, 'height': 768},
                'mobile': {'width': 320, 'height': 568}
            }
        },
        'analysis': {
            'max_concurrent': 2,
            'rate_limit_delay': 2,
            'dimensions': ['visual_design', 'user_experience']
        }
    }
    
    # Save custom config
    config_path = Path("examples/custom_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(custom_config, f, default_flow_style=False)
    
    # Use custom config
    analyzer = WebsiteAnalyzer(str(config_path))
    
    results = await analyzer.analyze_website(
        url="https://example.com",
        max_pages=2,
        output_dir="examples/reports/custom_config",
        report_format="json"
    )
    
    print(f"✅ Custom analysis completed!")
    print(f"   📊 Configuration: {config_path}")
    print(f"   📁 Report: {results['report_path']}")
    print()


async def example_error_handling():
    """Example: Error handling and recovery."""
    
    print("🔍 Example 5: Error Handling")
    print("=" * 50)
    
    analyzer = WebsiteAnalyzer()
    
    # Test with invalid URL
    try:
        await analyzer.analyze_website(
            url="https://invalid-website-that-does-not-exist.com",
            max_pages=1
        )
    except Exception as e:
        print(f"❌ Expected error caught: {type(e).__name__}: {str(e)}")
    
    # Test batch with mixed valid/invalid URLs
    mixed_urls = [
        "https://example.com",
        "https://invalid-website.com",
        "https://httpbin.org"
    ]
    
    results = await analyzer.analyze_multiple_websites(
        urls=mixed_urls,
        max_pages_per_site=1,
        output_dir="examples/reports/error_handling"
    )
    
    print(f"✅ Mixed batch completed:")
    print(f"   ✅ Successful: {results['successful_count']}")
    print(f"   ❌ Failed: {results['failed_count']}")
    print()


async def example_performance_monitoring():
    """Example: Performance monitoring and metrics."""
    
    print("🔍 Example 6: Performance Monitoring")
    print("=" * 50)
    
    start_time = datetime.now()
    
    analyzer = WebsiteAnalyzer()
    
    # Monitor performance during analysis
    results = await analyzer.analyze_website(
        url="https://example.com",
        max_pages=5,
        output_dir="examples/reports/performance"
    )
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    # Calculate performance metrics
    pages_per_second = results['pages_analyzed'] / results['duration_seconds']
    
    print(f"✅ Performance metrics:")
    print(f"   📊 Total duration: {total_duration:.2f}s")
    print(f"   📊 Analysis duration: {results['duration_seconds']:.2f}s")
    print(f"   📊 Pages per second: {pages_per_second:.2f}")
    print(f"   📊 Average score: {results['summary'].get('overall_average', 0):.1f}")
    print()


async def example_json_output():
    """Example: Working with JSON output."""
    
    print("🔍 Example 7: JSON Output Processing")
    print("=" * 50)
    
    analyzer = WebsiteAnalyzer()
    
    # Generate JSON report
    results = await analyzer.analyze_website(
        url="https://example.com",
        max_pages=3,
        output_dir="examples/reports/json_output",
        report_format="json"
    )
    
    # Load and process JSON data
    json_file = Path(results['report_path'])
    if json_file.exists():
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ JSON data loaded:")
        print(f"   📊 Pages: {len(data.get('pages', []))}")
        print(f"   📊 Average scores: {data.get('summary', {}).get('average_scores', {})}")
        
        # Example: Extract specific data
        high_scoring_pages = [
            page for page in data.get('pages', [])
            if page.get('analysis', {}).get('overall_score', 0) > 80
        ]
        print(f"   📊 High-scoring pages: {len(high_scoring_pages)}")
    
    print()


async def main():
    """Run all examples."""
    
    print("🚀 Website Analyzer - Example Usage")
    print("=" * 70)
    print()
    
    # Create examples directory
    Path("examples/reports").mkdir(parents=True, exist_ok=True)
    
    try:
        # Run examples
        await example_single_site_analysis()
        await example_batch_analysis()
        await example_component_usage()
        await example_custom_configuration()
        await example_error_handling()
        await example_performance_monitoring()
        await example_json_output()
        
        print("🎉 All examples completed successfully!")
        print("📁 Check the 'examples/reports' directory for generated reports.")
        
    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
