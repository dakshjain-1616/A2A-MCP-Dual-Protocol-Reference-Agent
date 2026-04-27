"""Gradio UI - Three-panel dashboard for real-time monitoring."""

import asyncio
import json
from typing import Any

import gradio as gr
import httpx

from a2a_mcp_agent.config import get_settings
from a2a_mcp_agent.utils.logging import get_logger

logger = get_logger(__name__)


class AgentDashboard:
    """Gradio dashboard for monitoring the A2A MCP Agent."""
    
    def __init__(self) -> None:
        """Initialize the dashboard."""
        self.settings = get_settings()
        self.a2a_base_url = f"http://localhost:{self.settings.a2a_port}"
        self.conversation_history: list[dict[str, Any]] = []
        self.tool_calls_log: list[dict[str, Any]] = []
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface.
        
        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(title="A2A MCP Agent Dashboard", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🤖 A2A MCP Reference Agent Dashboard")
            gr.Markdown("Real-time monitoring and interaction with the dual-protocol agent")
            
            with gr.Row():
                # Left panel: Agent Status & Tools
                with gr.Column(scale=1):
                    gr.Markdown("## 📊 Agent Status")
                    status_box = gr.Textbox(
                        label="Status",
                        value="Checking...",
                        interactive=False,
                    )
                    
                    refresh_btn = gr.Button("🔄 Refresh Status")
                    
                    gr.Markdown("## 🛠️ Available Tools")
                    tools_box = gr.JSON(
                        label="Tools",
                        value={},
                    )
                    
                    gr.Markdown("## 📋 Agent Card")
                    agent_card_box = gr.JSON(
                        label="Agent Card",
                        value={},
                    )
                
                # Center panel: Chat Interface
                with gr.Column(scale=2):
                    gr.Markdown("## 💬 Chat with Agent")
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=400,
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="Message",
                            placeholder="Enter your message...",
                            scale=4,
                        )
                        send_btn = gr.Button("Send", scale=1)
                    
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Clear Chat")
                        stream_btn = gr.Button("📡 Stream Mode")
                
                # Right panel: Tool Calls & Logs
                with gr.Column(scale=1):
                    gr.Markdown("## 🔧 Recent Tool Calls")
                    tool_calls_box = gr.JSON(
                        label="Tool Calls",
                        value=[],
                    )
                    
                    gr.Markdown("## 📈 Metrics")
                    metrics_box = gr.JSON(
                        label="Metrics",
                        value={
                            "total_requests": 0,
                            "successful": 0,
                            "failed": 0,
                            "avg_response_time": "N/A",
                        },
                    )
                    
                    gr.Markdown("## 📝 System Logs")
                    logs_box = gr.Textbox(
                        label="Logs",
                        value="No logs yet...",
                        lines=10,
                        interactive=False,
                    )
            
            # Event handlers
            refresh_btn.click(
                fn=self._refresh_status,
                outputs=[status_box, tools_box, agent_card_box],
            )
            
            send_btn.click(
                fn=self._send_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, tool_calls_box, metrics_box, logs_box],
            ).then(
                fn=lambda: "",
                outputs=[msg_input],
            )
            
            msg_input.submit(
                fn=self._send_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, tool_calls_box, metrics_box, logs_box],
            ).then(
                fn=lambda: "",
                outputs=[msg_input],
            )
            
            clear_btn.click(
                fn=self._clear_chat,
                outputs=[chatbot],
            )
            
            stream_btn.click(
                fn=self._stream_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot],
            )
            
            # Load initial status
            demo.load(
                fn=self._refresh_status,
                outputs=[status_box, tools_box, agent_card_box],
            )
        
        return demo
    
    def _refresh_status(self) -> tuple[str, dict, dict]:
        """Refresh agent status."""
        try:
            response = httpx.get(f"{self.a2a_base_url}/health", timeout=5.0)
            if response.status_code == 200:
                status = "✅ Online"
            else:
                status = f"⚠️ Error ({response.status_code})"
        except Exception as e:
            status = f"❌ Offline: {str(e)}"
        
        # Get agent card
        try:
            response = httpx.get(f"{self.a2a_base_url}/.well-known/agent-card.json", timeout=5.0)
            agent_card = response.json() if response.status_code == 200 else {}
        except Exception:
            agent_card = {}
        
        tools = agent_card.get("tools", [])
        
        return status, {"tools": tools}, agent_card
    
    def _send_message(
        self, message: str, history: list[list[str]]
    ) -> tuple[list[list[str]], list, dict, str]:
        """Send message to agent."""
        if not message.strip():
            return history, [], self._get_metrics(), "No message provided"
        
        # Add user message to history
        history = history + [[message, None]]
        
        try:
            # Call A2A server
            task_request = {
                "id": f"task_{len(history)}",
                "message": {"role": "user", "content": message},
            }
            
            response = httpx.post(
                f"{self.a2a_base_url}/tasks/send",
                json=task_request,
                timeout=60.0,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("result", {}).get("content", "No response")
                tool_calls = result.get("metadata", {}).get("tool_results", [])
                
                # Update history
                history[-1][1] = content
                
                # Log tool calls
                self.tool_calls_log.extend(tool_calls)
                
                # Update metrics
                metrics = self._update_metrics(success=True)
                
                logs = f"Task completed. Tool calls: {len(tool_calls)}"
                
                return history, tool_calls, metrics, logs
            else:
                history[-1][1] = f"Error: {response.status_code}"
                metrics = self._update_metrics(success=False)
                return history, [], metrics, f"HTTP Error: {response.status_code}"
        
        except Exception as e:
            history[-1][1] = f"Error: {str(e)}"
            metrics = self._update_metrics(success=False)
            return history, [], metrics, f"Exception: {str(e)}"
    
    def _stream_message(self, message: str, history: list[list[str]]) -> list[list[str]]:
        """Stream message to agent."""
        if not message.strip():
            return history
        
        history = history + [[message, ""]]
        
        try:
            task_request = {
                "id": f"stream_task_{len(history)}",
                "message": {"role": "user", "content": message},
            }
            
            with httpx.stream(
                "POST",
                f"{self.a2a_base_url}/tasks/sendSubscribe",
                json=task_request,
                timeout=60.0,
            ) as response:
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content":
                            history[-1][1] += data.get("content", "")
                        elif data.get("type") == "status":
                            if data.get("status") == "completed":
                                break
            
            return history
        
        except Exception as e:
            history[-1][1] = f"Error: {str(e)}"
            return history
    
    def _clear_chat(self) -> list:
        """Clear chat history."""
        return []
    
    def _get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            "total_requests": len(self.conversation_history),
            "successful": sum(1 for r in self.conversation_history if r.get("success", False)),
            "failed": sum(1 for r in self.conversation_history if not r.get("success", False)),
            "tool_calls": len(self.tool_calls_log),
        }
    
    def _update_metrics(self, success: bool) -> dict:
        """Update and return metrics."""
        self.conversation_history.append({"success": success})
        return self._get_metrics()
    
    def run(self) -> None:
        """Run the Gradio interface."""
        demo = self.create_interface()
        demo.launch(
            server_name=self.settings.gradio_host,
            server_port=self.settings.gradio_port,
            share=self.settings.gradio_share,
            show_error=True,
        )


def main() -> None:
    """Main entry point."""
    dashboard = AgentDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
