"""Real-time dashboard using rich library."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from typing import Dict, List
from datetime import datetime


class TradingDashboard:
    """Real-time trading dashboard."""
    
    def __init__(self):
        """Initialize dashboard."""
        self.console = Console()
    
    def create_summary_table(self, results: Dict[str, Dict]) -> Table:
        """Create summary table of all trades."""
        table = Table(title="Trading Summary", show_header=True, header_style="bold magenta")
        
        table.add_column("Ticker", style="cyan", width=8)
        table.add_column("Price", justify="right", style="green")
        table.add_column("Change", justify="right")
        table.add_column("News Score", justify="center")
        table.add_column("Sentiment", justify="center")
        table.add_column("RSI", justify="right")
        table.add_column("Decision", justify="center", style="bold")
        table.add_column("Confidence", justify="center")
        
        for ticker, data in results.items():
            if data.get('error'):
                table.add_row(ticker, "ERROR", "-", "-", "-", "-", "-")
                continue
            
            market = data.get('market_data', {})
            sentiment = data.get('sentiment_data', {})
            technical = data.get('technical_data', {})
            decision = data.get('decision', {})
            
            # Format change with color
            change = market.get('change', 0)
            change_pct = market.get('percent_change', 0)
            change_str = f"${change:.2f} ({change_pct:+.2f}%)"
            change_style = "green" if change >= 0 else "red"
            
            # News score
            news_alert = data.get('news_alert', {})
            news_score = news_alert.get('score', 0.0)
            news_alert_flag = news_alert.get('alert', False)
            if news_alert_flag:
                news_str = f"[bold]{'🔴' if news_score < 0 else '🟢'} {news_score:+.3f}[/bold]"
            else:
                news_str = f"{news_score:+.3f}" if news_score != 0.0 else "-"

            # Sentiment emoji
            sentiment_map = {
                'positive': '[green]+ Positive[/green]',
                'negative': '[red]- Negative[/red]',
                'neutral': '~ Neutral'
            }
            sentiment_str = sentiment_map.get(sentiment.get('avg_sentiment', 'neutral'), 'neutral')
            
            # Decision styling
            decision_str = decision.get('decision', 'HOLD')
            decision_style = {
                'BUY': 'bold green',
                'SELL': 'bold red',
                'HOLD': 'bold yellow'
            }.get(decision_str, 'white')
            
            table.add_row(
                ticker,
                f"${market.get('current_price', 0):.2f}",
                f"[{change_style}]{change_str}[/{change_style}]",
                news_str,
                sentiment_str,
                f"{technical.get('indicators', {}).get('rsi', 0):.1f}",
                f"[{decision_style}]{decision_str}[/{decision_style}]",
                decision.get('confidence', 'LOW')
            )
        
        return table
    
    def create_detail_panel(self, ticker: str, data: Dict) -> Panel:
        """Create detailed panel for a single ticker."""
        if data.get('error'):
            return Panel(f"[red]Error: {data['error']}[/red]", title=ticker)
        
        decision = data.get('decision', {})
        sentiment = data.get('sentiment_data', {})
        technical = data.get('technical_data', {})
        news_alert = data.get('news_alert', {})

        news_line = ""
        if news_alert:
            score = news_alert.get('score', 0.0)
            direction = news_alert.get('direction', 'neutral').upper()
            count = news_alert.get('articles_count', 0)
            alert_tag = " ⚠️ ALERT" if news_alert.get('alert') else ""
            news_line = f"\n[bold yellow]Sentinel News:[/bold yellow] score={score:+.3f} ({direction}), {count} articles{alert_tag}"

        content = f"""
[bold cyan]Decision:[/bold cyan] {decision.get('decision', 'N/A')}
[bold cyan]Confidence:[/bold cyan] {decision.get('confidence', 'N/A')}
[bold cyan]Reasoning:[/bold cyan] {decision.get('reasoning', 'N/A')}
{news_line}
[bold yellow]Sentiment Analysis:[/bold yellow]
  Overall: {sentiment.get('avg_sentiment', 'N/A')} (Score: {sentiment.get('avg_score', 0):.3f})
  Positive: {sentiment.get('positive_ratio', 0):.1%} | Negative: {sentiment.get('negative_ratio', 0):.1%}

[bold yellow]Technical Indicators:[/bold yellow]
  RSI: {technical.get('indicators', {}).get('rsi', 0):.2f}
  MACD: {technical.get('indicators', {}).get('macd', {}).get('macd', 0):.4f}
  
[bold yellow]Analysis:[/bold yellow]
{technical.get('analysis', 'N/A')}
"""
        
        return Panel(content, title=f"[bold]{ticker}[/bold]", border_style="blue")
    
    def display_results(self, results: Dict[str, Dict]):
        """Display complete results."""
        self.console.clear()
        
        # Header
        self.console.print(Panel.fit(
            "[bold cyan]Trading Agents - Real-Time Analysis[/bold cyan]",
            subtitle=f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        ))
        
        # Summary table
        summary = self.create_summary_table(results)
        self.console.print(summary)
        self.console.print()
        
        # Detailed panels for each ticker
        for ticker, data in results.items():
            panel = self.create_detail_panel(ticker, data)
            self.console.print(panel)
            self.console.print()
    
    def display_monitoring_header(self, interval_minutes: int):
        """Display monitoring mode header."""
        self.console.print(Panel.fit(
            f"[bold green]Monitoring Mode Active[/bold green]\n"
            f"Running analysis every {interval_minutes} minutes\n"
            f"Press Ctrl+C to stop",
            border_style="green"
        ))
