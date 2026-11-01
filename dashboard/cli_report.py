"""
CLI Dashboard & Daily Execution Reporting
Displays rich terminal analytics and system status.
"""

from typing import Dict, Any
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from database.models import DatabaseManager
from youtube.scheduler import PublicationScheduler


class DashboardReporter:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.console = Console()

    def show_dashboard(self):
        """Renders rich dashboard to the console."""
        stats = self.db.get_dashboard_stats()
        tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p IST")

        # Next publications
        next_slots = PublicationScheduler.get_next_publication_slots(count=2)
        next_pub_str = ", ".join([slot[0].strftime("%I:%M %p (%d %b)") for slot in next_slots])

        # Header panel
        header = Panel(
            f"[bold yellow]🏏 CRICKET FACTS YOUTUBE SHORTS FACTORY[/bold yellow]\n"
            f"[dim]System Time: {now_ist} | Target: 2 Shorts/Day[/dim]",
            border_style="yellow"
        )
        self.console.print(header)

        # Metrics cards
        card_facts = Panel(
            f"[bold cyan]Facts Researched:[/bold cyan] {stats['total_facts']}\n"
            f"[bold green]Facts Approved:[/bold green] {stats['approved_facts']}\n"
            f"[bold magenta]Min Score Threshold:[/bold magenta] 80/100",
            title="[bold]Fact Engine[/bold]",
            border_style="cyan"
        )

        card_videos = Panel(
            f"[bold green]Videos Generated:[/bold green] {stats['total_shorts']}\n"
            f"[bold blue]Scheduled / Uploaded:[/bold blue] {stats['uploaded_shorts']}\n"
            f"[bold yellow]Pending Uploads:[/bold yellow] {stats['pending_uploads']}\n"
            f"[bold red]Failed QC:[/bold red] {stats['failed_qc']}",
            title="[bold]Production Pipeline[/bold]",
            border_style="green"
        )

        card_sched = Panel(
            f"[bold]Daily Publication Schedule:[/bold]\n"
            f"• Morning Slot: 11:00 AM IST\n"
            f"• Evening Slot: 07:00 PM IST\n\n"
            f"[bold yellow]Next Publishing Window:[/bold yellow]\n"
            f"{next_pub_str}",
            title="[bold]Scheduler Status[/bold]",
            border_style="magenta"
        )

        self.console.print(Columns([card_facts, card_videos, card_sched]))

        # Recent Shorts Table
        table = Table(title="Recent Generated Shorts & Publication Status", border_style="blue")
        table.add_column("ID", justify="center", style="dim", width=4)
        table.add_column("Topic", style="bold", width=36)
        table.add_column("Title", width=38)
        table.add_column("Status", justify="center")
        table.add_column("Scheduled Time", justify="center", width=22)

        for s in stats["recent_shorts"]:
            status_style = "green" if s["upload_status"] in ("SCHEDULED", "QC_PASSED") else "yellow"
            table.add_row(
                str(s["id"]),
                s["topic"][:34],
                (s["title"] or "")[:36],
                f"[{status_style}]{s['upload_status']}[/{status_style}]",
                s["scheduled_publish_time"] or "N/A"
            )

        if not stats["recent_shorts"]:
            table.add_row("-", "No shorts generated yet", "-", "PENDING", "-")

        self.console.print(table)
