"""
Main entry point for the Core Network DevOps Agent

This module provides the CLI interface following AgentCore framework patterns.
"""

import asyncio
import sys
from pathlib import Path
import yaml
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import structlog

from .core_agent import CoreNetworkDevOpsAgent
from .utils.aws_client import AWSClientManager

# Configure console
console = Console()
logger = structlog.get_logger(__name__)


def load_config(config_path: str = None) -> dict:
    """Load agent configuration from YAML file."""
    if config_path is None:
        # Look for config in standard locations
        possible_paths = [
            Path("config/agent_config.yaml"),
            Path("agent_config.yaml"),
            Path.home() / ".core-network-agent" / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            # Return default configuration
            return {
                "agent": {
                    "model": {
                        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "region": "us-east-1"
                    }
                }
            }
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        console.print(f"[green]✅ Loaded configuration from {config_path}[/green]")
        return config
    except Exception as e:
        console.print(f"[red]❌ Failed to load config from {config_path}: {e}[/red]")
        sys.exit(1)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Core Network DevOps Agent - AI-powered network infrastructure management."""
    
    # Configure logging
    if verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    # Load configuration
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.pass_context
def chat(ctx):
    """Start interactive chat mode with the agent."""
    config = ctx.obj['config']
    
    # Display welcome message
    console.print(Panel(
        "[bold cyan]🤖 Core Network DevOps Agent[/bold cyan]\n\n"
        "AI-powered assistant for core network infrastructure and DevOps operations.\n"
        "Type 'help' for available commands or 'exit' to quit.\n\n"
        "[dim]Powered by Amazon Bedrock AgentCore Framework[/dim]",
        title="Welcome",
        border_style="cyan"
    ))
    
    # Initialize agent
    try:
        model_config = config.get('agent', {}).get('model', {})
        agent = CoreNetworkDevOpsAgent(
            name=config.get('agent', {}).get('name', 'CoreNetworkDevOpsAgent'),
            model_id=model_config.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            region=model_config.get('region', 'us-east-1'),
            config=config
        )
        
        # Initialize the agent
        asyncio.run(agent.initialize())
        
        # Verify AWS connectivity
        aws_manager = AWSClientManager(region=model_config.get('region', 'us-east-1'))
        cred_info = aws_manager.validate_credentials()
        
        if cred_info['valid']:
            console.print(Panel(
                f"[green]✅ AWS Connection Verified[/green]\n"
                f"Account: [bold]{cred_info['account_id']}[/bold]\n"
                f"Region: [bold]{cred_info['region']}[/bold]\n"
                f"User: [dim]{cred_info['arn']}[/dim]",
                title="AWS Status",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]❌ AWS Connection Failed[/red]\n"
                f"Error: {cred_info['error']}\n\n"
                "Please configure your AWS credentials.",
                title="AWS Error",
                border_style="red"
            ))
            return
        
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize agent: {e}[/red]")
        return
    
    # Start chat loop
    asyncio.run(chat_loop(agent))


async def chat_loop(agent: CoreNetworkDevOpsAgent):
    """Main chat interaction loop."""
    
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]core-network-agent>[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("[yellow]👋 Goodbye![/yellow]")
                break
            elif user_input.lower() == 'help':
                show_help()
                continue
            elif user_input.lower() == 'status':
                await show_status(agent)
                continue
            elif user_input.lower() == 'history':
                show_history(agent)
                continue
            elif user_input.lower() == 'clear':
                agent.clear_conversation_history()
                console.print("[green]✅ Conversation history cleared[/green]")
                continue
            
            # Process request with agent
            console.print("[yellow]🤔 Processing your request...[/yellow]")
            
            response = await agent.process_request(user_input)
            
            if response.success:
                console.print(Panel(
                    response.content,
                    title="🤖 Agent Response",
                    border_style="blue"
                ))
                
                # Show tool results if available
                if response.tool_results:
                    show_tool_results(response.tool_results)
            else:
                console.print(Panel(
                    f"[red]❌ Error: {response.content}[/red]",
                    title="Error",
                    border_style="red"
                ))
                
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Unexpected error: {e}[/red]")


def show_help():
    """Display help information."""
    help_text = """
[bold]Available Commands:[/bold]

[cyan]General Commands:[/cyan]
• help - Show this help message
• status - Show agent and system status
• history - Show conversation history
• clear - Clear conversation history
• exit/quit - Exit the chat

[cyan]Example Requests:[/cyan]
• "List all EC2 instances in us-east-1"
• "Create a VPC with CIDR 10.0.0.0/16"
• "Deploy AMF with 3 replicas"
• "Show me the status of all network functions"
• "Create an EKS cluster for 5G core"
• "Set up monitoring for the core network"

[cyan]Network Functions:[/cyan]
• AMF (Access and Mobility Management Function)
• SMF (Session Management Function)
• UPF (User Plane Function)
• AUSF, UDM, UDR, NRF, NSSF, PCF

[cyan]Infrastructure Operations:[/cyan]
• EC2 instances and VPCs
• EKS clusters and node groups
• Load balancers and security groups
• Monitoring and logging setup
    """
    console.print(Panel(help_text, title="Help", border_style="cyan"))


async def show_status(agent: CoreNetworkDevOpsAgent):
    """Show agent and system status."""
    console.print("[yellow]🔍 Checking system status...[/yellow]")
    
    # Get health check
    health = await agent.health_check()
    
    # Create status table
    table = Table(title="System Status", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    # Agent status
    agent_status = "🟢 Healthy" if health['status'] == 'healthy' else "🟡 Degraded"
    table.add_row("Agent", agent_status, f"Model: {health['model_id']}")
    
    # Tool health statuses
    for tool_name, tool_status in health.get('tool_health', {}).items():
        if isinstance(tool_status, dict) and tool_status.get('status') == 'error':
            status_icon = "🔴 Error"
            details = tool_status.get('error', 'Unknown error')
        else:
            status_icon = "🟢 Healthy"
            details = "Available"
        
        table.add_row(f"Tool: {tool_name}", status_icon, details)
    
    console.print(table)
    
    # Show available tools
    tools = list(agent.get_tools().keys())
    console.print(f"\n[cyan]Available Tools:[/cyan] {', '.join(tools)}")


def show_history(agent: CoreNetworkDevOpsAgent):
    """Show conversation history."""
    history = agent.get_conversation_history()
    
    if not history:
        console.print("[yellow]No conversation history available[/yellow]")
        return
    
    console.print(Panel(
        f"[bold]Conversation History ({len(history)} messages)[/bold]",
        border_style="blue"
    ))
    
    for i, message in enumerate(history[-10:], 1):  # Show last 10 messages
        role = message['role']
        content = message['content'][:200] + "..." if len(message['content']) > 200 else message['content']
        timestamp = message['timestamp']
        
        role_color = "cyan" if role == "user" else "blue"
        console.print(f"[{role_color}]{i}. {role.title()}:[/{role_color}] {content}")
        console.print(f"[dim]   {timestamp}[/dim]\n")


def show_tool_results(tool_results: dict):
    """Display tool execution results."""
    if not tool_results:
        return
    
    console.print("\n[bold]Tool Execution Results:[/bold]")
    
    for tool_name, result in tool_results.items():
        if result.get('success', False):
            console.print(f"[green]✅ {tool_name}:[/green] {result.get('action', 'completed')}")
            
            # Show data summary if available
            if 'data' in result:
                data = result['data']
                if isinstance(data, dict) and 'count' in data:
                    console.print(f"   [dim]Found {data['count']} items[/dim]")
        else:
            console.print(f"[red]❌ {tool_name}:[/red] {result.get('error', 'Failed')}")


@cli.command()
@click.pass_context
def health(ctx):
    """Check agent and system health."""
    config = ctx.obj['config']
    
    try:
        model_config = config.get('agent', {}).get('model', {})
        agent = CoreNetworkDevOpsAgent(
            name=config.get('agent', {}).get('name', 'CoreNetworkDevOpsAgent'),
            model_id=model_config.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            region=model_config.get('region', 'us-east-1'),
            config=config
        )
        
        asyncio.run(agent.initialize())
        health = asyncio.run(agent.health_check())
        
        if health['status'] == 'healthy':
            console.print("[green]✅ Agent is healthy[/green]")
            sys.exit(0)
        else:
            console.print("[yellow]⚠️ Agent is degraded[/yellow]")
            for tool_name, tool_status in health.get('tool_health', {}).items():
                console.print(f"  {tool_name}: {tool_status}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Health check failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Choice(['json', 'yaml', 'table']), default='table')
@click.pass_context
def info(ctx, output):
    """Show agent information and configuration."""
    config = ctx.obj['config']
    
    info_data = {
        'agent': {
            'name': 'Core Network DevOps Agent',
            'version': '1.0.0',
            'framework': 'Amazon Bedrock AgentCore'
        },
        'model': config.get('agent', {}).get('model', {}),
        'tools': config.get('tools', {}),
        'aws': config.get('aws', {}),
        'kubernetes': config.get('kubernetes', {})
    }
    
    if output == 'json':
        import json
        console.print(json.dumps(info_data, indent=2))
    elif output == 'yaml':
        console.print(yaml.dump(info_data, default_flow_style=False))
    else:
        # Table format
        table = Table(title="Agent Information", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Key", style="green")
        table.add_column("Value", style="white")
        
        def add_dict_to_table(data, category=""):
            for key, value in data.items():
                if isinstance(value, dict):
                    add_dict_to_table(value, f"{category}.{key}" if category else key)
                else:
                    table.add_row(category, key, str(value))
        
        add_dict_to_table(info_data)
        console.print(table)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()