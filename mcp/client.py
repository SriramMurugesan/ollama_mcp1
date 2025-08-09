import json
import re

class MCPClient:
    def __init__(self):
        self.tools = {}

    def register_tool(self, name, config):
        self.tools[name] = config

    def parse_for_tool(self, message):
        """
        Parse message for tool calls with improved detection
        """
        if not isinstance(message, str):
            return None
            
        # Look for tool call patterns like "use hubspot" or "call hubspot-mcp"
        tool_patterns = [
            r'use\s+(\w+(?:-\w+)*)',
            r'call\s+(\w+(?:-\w+)*)',
            r'(\w+(?:-\w+)*)\s+tool',
            r'(hubspot-mcp)',
        ]
        
        for pattern in tool_patterns:
            match = re.search(pattern, message.lower())
            if match:
                tool_name = match.group(1)
                if tool_name in self.tools:
                    return {"tool": tool_name, "params": {}}
        
        # Also check for exact tool name mentions
        for tool_name in self.tools:
            if tool_name.lower() in message.lower():
                return {"tool": tool_name, "params": {}}
                
        return None

    def call_tool(self, tool_request):
       
        tool = tool_request["tool"]
        config = self.tools.get(tool, {})
        
        if tool == "hubspot-mcp":
            return f"[HubSpot MCP tool called successfully]"
        else:
            return f"[Simulated tool '{tool}' output with config: {json.dumps(config, indent=2)}]"
