#!/usr/bin/env python3
import sys
import subprocess
import time
import os
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.prompt import Prompt, IntPrompt

# Initial Configuration
CONFIG = {
    "host": "127.0.0.1",
    "port": 8888
}

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_version():
    try:
        commit_count = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip())
        
        major = commit_count // 100
        minor = (commit_count % 100) // 10
        patch = commit_count % 10
        return f"v{major}.{minor}.{patch}"
    except:
        return "v1.0.0"

def print_banner():
    clear_screen()
    banner_text = r"""
    ███████                                      ██████   █████           █████   
    ███░░░░░███                                   ░░██████ ░░███           ░░███    
   ███     ░░███ ████████   █████ ████ █████ █████ ░███░███ ░███   ██████  ███████  
  ░███      ░███░░███░░███ ░░███ ░███ ░░███ ░░███  ░███░░███░███  ███░░███░░░███░   
  ░███      ░███ ░███ ░███  ░███ ░███  ░░░█████░   ░███ ░░██████ ░███████   ░███    
  ░░███     ███  ░███ ░███  ░███ ░███   ███░░░███  ░███  ░░█████ ░███░░░    ░███ ███
   ░░░███████░   ████ █████ ░░███████  █████ █████ █████  ░░█████░░██████   ░░█████ 
     ░░░░░░░    ░░░░ ░░░░░   ░░░░░███ ░░░░░ ░░░░░ ░░░░░    ░░░░░  ░░░░░░     ░░░░░  
                             ███ ░███                                               
                            ░░██████                                                
                             ░░░░░░                                                 
    """
    
    version = get_version()
    
    panel = Panel(
        Align.center(f"[bold green]{banner_text}[/bold green]\n[cyan]Secure Hacker Chat[/cyan] {version}"),
        border_style="green",
        expand=False
    )
    console.print(panel)
    console.print(f"[bold yellow]Current Config:[/bold yellow] [blue]{CONFIG['host']}:{CONFIG['port']}[/blue]")
    console.print("-" * 50, style="dim")

def start_server():
    console.print("[green][*] Starting Relay Server...[/green]")
    cmd = [sys.executable, "-m", "server.main", "--host", CONFIG['host'], "--port", str(CONFIG['port'])]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

def start_client():
    console.print("[green][*] Starting Terminal Client...[/green]")
    cmd = [sys.executable, "-m", "client.main", "--host", CONFIG['host'], "--port", str(CONFIG['port'])]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

def start_web():
    console.print("[green][*] Starting Web Server...[/green]")
    # start_web.py needs to be updated to accept args if we want it to be dynamic too, 
    # but for now let's minimal launch. 
    # Actually start_web.py is minimal simple http.server
    # For now let's just run it standard.
    cmd = [sys.executable, "start_web.py"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass


def configure():
    console.print("[bold cyan]Configuration[/bold cyan]")
    CONFIG['host'] = Prompt.ask("Host", default=CONFIG['host'])
    CONFIG['port'] = IntPrompt.ask("Port", default=CONFIG['port'])
    console.print("[green]Configuration Updated![/green]")
    time.sleep(1)

def main():
    while True:
        print_banner()
        console.print("[1] Start Relay Server")
        console.print("[2] Start Terminal Client")
        console.print("[3] Start Web Server")
        console.print("[4] Configure Host/Port")
        console.print("[0] Exit")
        console.print("")
        
        choice = Prompt.ask("Select Option", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "1":
            start_server()
        elif choice == "2":
            start_client()
        elif choice == "3":
            start_web()
        elif choice == "4":
            configure()
        elif choice == "0":
            console.print("[bold red]Exiting...[/bold red]")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye.")
