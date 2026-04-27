"""Command-line interface for A2A MCP Agent."""

import asyncio
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.json import JSON as RichJSON
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from a2a_mcp_agent.agent import Agent
from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, mock: bool) -> None:
    """A2A MCP Reference Agent CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["mock"] = mock
    
    setup_logging()
    
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    if mock:
        console.print("[yellow]Running in mock mode[/yellow]")


@cli.command()
@click.option("--host", "-h", default=None, help="Host to bind to")
@click.option("--port", "-p", type=int, default=None, help="Port to listen on")
@click.pass_context
def serve_a2a(ctx: click.Context, host: str | None, port: int | None) -> None:
    """Start the A2A server."""
    import uvicorn
    
    settings = get_settings()
    host = host or settings.a2a_host
    port = port or settings.a2a_port
    
    console.print(Panel.fit(
        f"[bold green]Starting A2A Server[/bold green]\n"
        f"Host: {host}\nPort: {port}",
        title="A2A MCP Agent",
    ))
    
    uvicorn.run(
        "a2a_mcp_agent.a2a_server:app",
        host=host,
        port=port,
        reload=settings.a2a_debug,
    )


@cli.command()
@click.option("--host", "-h", default=None, help="Host to bind to")
@click.option("--port", "-p", type=int, default=None, help="Port to listen on")
@click.pass_context
def serve_ui(ctx: click.Context, host: str | None, port: int | None) -> None:
    """Start the Gradio UI server."""
    from a2a_mcp_agent.ui import AgentDashboard
    
    settings = get_settings()
    
    # Override settings
    if host:
        settings.gradio_host = host
    if port:
        settings.gradio_port = port
    
    console.print(Panel.fit(
        f"[bold green]Starting Gradio UI[/bold green]\n"
        f"URL: http://{settings.gradio_host}:{settings.gradio_port}",
        title="A2A MCP Agent",
    ))
    
    dashboard = AgentDashboard()
    dashboard.run()


@cli.command()
@click.option("--query", "-q", required=True, help="Research query")
@click.option("--web", is_flag=True, default=True, help="Use web search")
@click.option("--github", is_flag=True, default=True, help="Use GitHub search")
@click.pass_context
def research(ctx: click.Context, query: str, web: bool, github: bool) -> None:
    """Perform a research task."""
    
    async def run_research() -> None:
        agent = Agent(mock_mode=ctx.obj.get("mock", False))
        await agent.initialize()
        
        with console.status("[bold green]Researching..."):
            result = await agent.research(query, use_web_search=web, use_github=github)
        
        # Display results
        console.print(Panel.fit(
            f"[bold]Query:[/bold] {query}\n\n"
            f"[bold]Response:[/bold]\n{result.get('response', 'No response')}",
            title="Research Results",
        ))
        
        if result.get("tool_calls_executed", 0) > 0:
            console.print(f"\n[dim]Tool calls executed: {result['tool_calls_executed']}[/dim]")
            for tool_result in result.get("tool_results", []):
                if tool_result.get("success"):
                    console.print(f"  ✓ {tool_result['tool_name']}")
                else:
                    console.print(f"  ✗ {tool_result['tool_name']}: {tool_result.get('content', '')}")
        
        await agent.close()
    
    asyncio.run(run_research())


@cli.command()
@click.argument("message")
@click.pass_context
def chat(ctx: click.Context, message: str) -> None:
    """Send a single chat message to the agent."""
    
    async def run_chat() -> None:
        agent = Agent(mock_mode=ctx.obj.get("mock", False))
        await agent.initialize()
        
        with console.status("[bold green]Thinking..."):
            result = await agent.process_task(message)
        
        console.print(Panel.fit(
            f"[bold blue]You:[/bold blue] {message}\n\n"
            f"[bold green]Agent:[/bold green] {result.get('response', 'No response')}",
            title="Chat",
        ))
        
        if ctx.obj.get("verbose"):
            console.print("\n[dim]Full result:[/dim]")
            console.print(RichJSON(json.dumps(result, indent=2)))
        
        await agent.close()
    
    asyncio.run(run_chat())


@cli.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """Start interactive chat mode."""
    
    async def run_interactive() -> None:
        agent = Agent(mock_mode=ctx.obj.get("mock", False))
        await agent.initialize()
        
        console.print(Panel.fit(
            "[bold green]Interactive Chat Mode[/bold green]\n"
            "Type 'exit' or 'quit' to exit",
            title="A2A MCP Agent",
        ))
        
        while True:
            try:
                message = console.input("[bold blue]You:[/bold blue] ")
                
                if message.lower() in ("exit", "quit", "q"):
                    break
                
                if not message.strip():
                    continue
                
                with console.status("[bold green]Thinking..."):
                    result = await agent.process_task(message)
                
                console.print(f"[bold green]Agent:[/bold green] {result.get('response', 'No response')}\n")
                
                if result.get("tool_calls_executed", 0) > 0:
                    console.print(f"[dim](Used {result['tool_calls_executed']} tools)[/dim]\n")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
            except EOFError:
                break
        
        await agent.close()
        console.print("[dim]Goodbye![/dim]")
    
    asyncio.run(run_interactive())


@cli.command()
def status() -> None:
    """Check agent status."""
    import httpx
    
    settings = get_settings()
    
    table = Table(title="A2A MCP Agent Status")
    table.add_column("Service", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Status", style="green")
    
    # Check A2A server
    a2a_url = f"http://localhost:{settings.a2a_port}"
    try:
        response = httpx.get(f"{a2a_url}/health", timeout=5.0)
        a2a_status = "✅ Online" if response.status_code == 200 else f"⚠️ {response.status_code}"
    except Exception as e:
        a2a_status = f"❌ {str(e)[:30]}"
    
    table.add_row("A2A Server", a2a_url, a2a_status)
    
    # Check Agent Card
    try:
        response = httpx.get(f"{a2a_url}/.well-known/agent-card.json", timeout=5.0)
        card_status = "✅ Available" if response.status_code == 200 else f"⚠️ {response.status_code}"
    except Exception as e:
        card_status = f"❌ {str(e)[:30]}"
    
    table.add_row("Agent Card", f"{a2a_url}/.well-known/agent-card.json", card_status)
    
    # UI status
    ui_url = f"http://localhost:{settings.gradio_port}"
    table.add_row("Gradio UI", ui_url, "ℹ️ Check manually")
    
    console.print(table)
    
    # Show configuration
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Mock Mode: {settings.is_mock_mode}")
    console.print(f"  Log Level: {settings.log_level}")
    console.print(f"  DeepSeek Model: {settings.deepseek_model}")


@cli.command()
def tools() -> None:
    """List available tools."""
    import httpx
    
    settings = get_settings()
    a2a_url = f"http://localhost:{settings.a2a_port}"
    
    try:
        response = httpx.get(f"{a2a_url}/.well-known/agent-card.json", timeout=5.0)
        if response.status_code == 200:
            card = response.json()
            tools = card.get("tools", [])
            
            table = Table(title="Available Tools")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            
            for tool in tools:
                table.add_row(
                    tool.get("name", "unknown"),
                    tool.get("description", "No description")[:60],
                )
            
            console.print(table)
        else:
            console.print(f"[red]Error: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
