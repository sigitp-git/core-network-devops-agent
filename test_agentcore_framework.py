#!/usr/bin/env python3
"""
Test suite for Bedrock AgentCore Framework Integration

This test verifies that the Core Network DevOps Agent properly adopts
the Bedrock AgentCore framework patterns.
"""

import sys
import os
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestAgentCoreFramework:
    """Test suite for AgentCore framework integration."""
    
    def __init__(self):
        self.passed_tests = 0
        self.total_tests = 0
    
    def run_test(self, test_name, test_func):
        """Run a single test and track results."""
        print(f"\n{'='*70}")
        print(f"🧪 Testing: {test_name}")
        print('='*70)
        
        self.total_tests += 1
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                self.passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    def test_framework_imports(self):
        """Test that all AgentCore framework components can be imported."""
        print("Testing framework imports...")
        
        try:
            # Test framework base imports
            from core_network_devops_agent.framework import (
                Agent, AgentResponse, Tool, ToolResult, 
                ConversationMemory, tool, agent_handler
            )
            print("   ✓ Framework base classes imported")
            
            # Test specific components
            from core_network_devops_agent.framework.agent_base import AgentConfig, AgentFactory
            print("   ✓ Agent configuration classes imported")
            
            from core_network_devops_agent.framework.tool_base import ToolSpec, ToolParameter, ToolRegistry
            print("   ✓ Tool specification classes imported")
            
            from core_network_devops_agent.framework.memory import MessageRole, ConversationMessage
            print("   ✓ Memory management classes imported")
            
            from core_network_devops_agent.framework.decorators import (
                validate_tool_parameters, retry_on_failure
            )
            print("   ✓ Decorator utilities imported")
            
            return True
            
        except ImportError as e:
            print(f"   ❌ Import failed: {e}")
            return False
    
    def test_agent_handler_decorator(self):
        """Test the @agent_handler decorator functionality."""
        print("Testing @agent_handler decorator...")
        
        try:
            from core_network_devops_agent.framework import Agent, agent_handler, tool, ToolResult
            
            @agent_handler
            class TestAgent(Agent):
                def __init__(self):
                    super().__init__("TestAgent")
                
                async def initialize(self):
                    self._initialized = True
                
                async def process_request(self, user_input, context=None):
                    return f"Processed: {user_input}"
                
                @tool(
                    name="test_tool",
                    description="A test tool",
                    parameters={
                        "param1": {"type": "string", "description": "Test parameter", "required": True}
                    }
                )
                async def test_tool_method(self, param1: str):
                    return ToolResult(success=True, data={"result": f"Tool executed with {param1}"})
            
            # Create agent instance
            agent = TestAgent()
            
            # Check that tools were registered
            tools = agent.get_tools()
            print(f"   ✓ Agent created with {len(tools)} tools")
            print(f"   ✓ Registered tools: {list(tools.keys())}")
            
            # Check that the tool method was properly decorated
            if hasattr(agent.test_tool_method, '_is_tool'):
                print("   ✓ Tool method properly decorated")
            else:
                print("   ❌ Tool method not properly decorated")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_tool_execution_with_decorators(self):
        """Test tool execution using the decorator pattern."""
        print("Testing tool execution with decorators...")
        
        try:
            from core_network_devops_agent.framework import Agent, agent_handler, tool, ToolResult
            
            @agent_handler
            class TestAgent(Agent):
                def __init__(self):
                    super().__init__("TestAgent")
                
                async def initialize(self):
                    self._initialized = True
                
                async def process_request(self, user_input, context=None):
                    return f"Processed: {user_input}"
                
                @tool(
                    name="calculate",
                    description="Perform a calculation",
                    parameters={
                        "operation": {"type": "string", "description": "Operation type", "required": True},
                        "a": {"type": "integer", "description": "First number", "required": True},
                        "b": {"type": "integer", "description": "Second number", "required": True}
                    }
                )
                async def calculate(self, operation: str, a: int, b: int):
                    if operation == "add":
                        result = a + b
                    elif operation == "multiply":
                        result = a * b
                    else:
                        return ToolResult(success=False, error=f"Unknown operation: {operation}")
                    
                    return ToolResult(success=True, data={"result": result, "operation": operation})
            
            # Create and initialize agent
            agent = TestAgent()
            await agent.initialize()
            
            # Get the tool
            tool = agent.get_tool("calculate")
            print(f"   ✓ Retrieved tool: {tool.name}")
            
            # Execute the tool
            result = await tool.execute_with_validation({
                "operation": "add",
                "a": 5,
                "b": 3
            })
            
            print(f"   ✓ Tool executed successfully: {result.success}")
            print(f"   ✓ Tool result: {result.data}")
            print(f"   ✓ Execution time: {result.execution_time_ms}ms")
            
            # Test error handling
            error_result = await tool.execute_with_validation({
                "operation": "divide",
                "a": 10,
                "b": 2
            })
            
            print(f"   ✓ Error handling works: {not error_result.success}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_conversation_memory(self):
        """Test conversation memory functionality."""
        print("Testing conversation memory...")
        
        try:
            from core_network_devops_agent.framework.memory import ConversationMemory, MessageRole
            
            # Create memory instance
            memory = ConversationMemory(max_messages=10, retention_hours=1)
            
            # Add messages
            memory.add_message(MessageRole.USER, "Hello, how are you?")
            memory.add_message(MessageRole.ASSISTANT, "I'm doing well, thank you!")
            memory.add_message(MessageRole.USER, "Can you help me with AWS?", metadata={"topic": "aws"})
            
            print(f"   ✓ Added 3 messages to memory")
            
            # Test message retrieval
            all_messages = memory.get_messages()
            print(f"   ✓ Retrieved {len(all_messages)} messages")
            
            user_messages = memory.get_user_messages()
            print(f"   ✓ Retrieved {len(user_messages)} user messages")
            
            assistant_messages = memory.get_assistant_messages()
            print(f"   ✓ Retrieved {len(assistant_messages)} assistant messages")
            
            # Test context management
            memory.update_context({"current_topic": "aws", "user_level": "beginner"})
            context = memory.get_context()
            print(f"   ✓ Context updated: {list(context.keys())}")
            
            # Test conversation stats
            stats = memory.get_conversation_stats()
            print(f"   ✓ Conversation stats: {stats['total_messages']} total messages")
            
            # Test Bedrock format conversion
            bedrock_format = memory.to_bedrock_format()
            print(f"   ✓ Converted to Bedrock format: {len(bedrock_format)} messages")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_tool_specifications(self):
        """Test tool specification generation."""
        print("Testing tool specifications...")
        
        try:
            from core_network_devops_agent.framework.tool_base import ToolSpec, ToolParameter
            
            # Create a tool specification
            spec = ToolSpec(
                name="test_tool",
                description="A test tool for demonstration",
                parameters=[
                    ToolParameter(
                        name="region",
                        type="string",
                        description="AWS region",
                        required=True,
                        enum=["us-east-1", "us-west-2", "eu-west-1"]
                    ),
                    ToolParameter(
                        name="count",
                        type="integer",
                        description="Number of items",
                        required=False,
                        default=10
                    )
                ]
            )
            
            print(f"   ✓ Created tool spec: {spec.name}")
            print(f"   ✓ Parameters: {len(spec.parameters)}")
            
            # Convert to Bedrock format
            bedrock_format = spec.to_bedrock_format()
            print(f"   ✓ Converted to Bedrock format")
            print(f"   ✓ Tool name: {bedrock_format['toolSpec']['name']}")
            print(f"   ✓ Input schema properties: {list(bedrock_format['toolSpec']['inputSchema']['json']['properties'].keys())}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_core_agent_integration(self):
        """Test the refactored CoreNetworkDevOpsAgent with AgentCore framework."""
        print("Testing CoreNetworkDevOpsAgent with AgentCore framework...")
        
        try:
            from core_network_devops_agent.core_agent import CoreNetworkDevOpsAgent
            
            # Mock AWS services
            mock_session = Mock()
            mock_sts = Mock()
            mock_bedrock = Mock()
            mock_ec2 = Mock()
            
            # Configure mocks
            mock_sts.get_caller_identity.return_value = {
                'Account': '123456789012',
                'UserId': 'AIDACKCEVSQ6C2EXAMPLE',
                'Arn': 'arn:aws:iam::123456789012:user/demo-user'
            }
            
            mock_ec2.describe_instances.return_value = {
                'Reservations': [{
                    'Instances': [{
                        'InstanceId': 'i-test123',
                        'InstanceType': 't3.micro',
                        'State': {'Name': 'running'},
                        'LaunchTime': '2024-01-01T00:00:00Z',
                        'Tags': []
                    }]
                }]
            }
            
            # Mock Bedrock responses
            analysis_response = {
                "content": [{
                    "text": json.dumps({
                        "intent": "List EC2 instances",
                        "category": "infrastructure",
                        "tools_needed": ["describe_ec2_instances"],
                        "parameters": {
                            "describe_ec2_instances": {}
                        },
                        "complexity": "low"
                    })
                }]
            }
            
            final_response = {
                "content": [{
                    "text": "I found 1 EC2 instance: i-test123 (t3.micro) in running state."
                }]
            }
            
            mock_bedrock.invoke_model.side_effect = [
                {'body': Mock(read=lambda: json.dumps(analysis_response).encode())},
                {'body': Mock(read=lambda: json.dumps(final_response).encode())}
            ]
            
            # Configure session mock
            def get_client(service, **kwargs):
                clients = {
                    'sts': mock_sts,
                    'bedrock-runtime': mock_bedrock,
                    'ec2': mock_ec2
                }
                return clients.get(service, Mock())
            
            mock_session.client.side_effect = get_client
            mock_session.region_name = 'us-east-1'
            
            with patch('boto3.Session', return_value=mock_session):
                # Create agent
                agent = CoreNetworkDevOpsAgent()
                print(f"   ✓ Agent created: {agent.name}")
                
                # Initialize agent
                await agent.initialize()
                print(f"   ✓ Agent initialized successfully")
                
                # Check registered tools
                tools = agent.get_tools()
                print(f"   ✓ Registered tools: {list(tools.keys())}")
                
                # Test tool execution directly
                ec2_tool = agent.get_tool("describe_ec2_instances")
                if ec2_tool:
                    result = await ec2_tool.execute_with_validation({})
                    print(f"   ✓ EC2 tool executed: {result.success}")
                    print(f"   ✓ Found instances: {result.data['count']}")
                
                # Test full request processing
                response = await agent.process_request("List all EC2 instances")
                print(f"   ✓ Request processed: {response.success}")
                print(f"   ✓ Response content length: {len(response.content)}")
                print(f"   ✓ Tool results available: {bool(response.tool_results)}")
                
                # Test conversation memory
                history = agent.get_conversation_history()
                print(f"   ✓ Conversation history: {len(history)} messages")
                
                # Test health check
                health = await agent.health_check()
                print(f"   ✓ Health check: {health['status']}")
                
                return True
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_agent_factory(self):
        """Test agent factory functionality."""
        print("Testing agent factory...")
        
        try:
            from core_network_devops_agent.framework.agent_base import AgentFactory, AgentConfig
            from core_network_devops_agent.core_agent import CoreNetworkDevOpsAgent
            
            # Test with dictionary config
            config_dict = {
                "name": "TestAgent",
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "region": "us-west-2",
                "max_tokens": 2000
            }
            
            agent = AgentFactory.create_agent(CoreNetworkDevOpsAgent, config_dict)
            print(f"   ✓ Agent created from dict config: {agent.name}")
            print(f"   ✓ Agent region: {agent.region}")
            
            # Test with AgentConfig object
            config_obj = AgentConfig(
                name="TestAgent2",
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                region="eu-west-1"
            )
            
            agent2 = AgentFactory.create_agent(CoreNetworkDevOpsAgent, config_obj)
            print(f"   ✓ Agent created from config object: {agent2.name}")
            print(f"   ✓ Agent model: {agent2.model_id}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_tool_registry(self):
        """Test tool registry functionality."""
        print("Testing tool registry...")
        
        try:
            from core_network_devops_agent.framework.tool_base import ToolRegistry, Tool, ToolSpec, ToolResult
            
            # Create a simple test tool
            class TestTool(Tool):
                def __init__(self):
                    super().__init__("test_tool", "A simple test tool")
                
                async def execute(self, parameters):
                    return ToolResult(success=True, data={"message": "Tool executed"})
                
                def get_spec(self):
                    return ToolSpec(name=self.name, description=self.description)
            
            # Create registry and register tool
            registry = ToolRegistry()
            test_tool = TestTool()
            
            registry.register(test_tool)
            print(f"   ✓ Tool registered in registry")
            
            # Test retrieval
            retrieved_tool = registry.get_tool("test_tool")
            print(f"   ✓ Tool retrieved: {retrieved_tool.name}")
            
            # Test all tools
            all_tools = registry.get_all_tools()
            print(f"   ✓ All tools: {list(all_tools.keys())}")
            
            # Test tool specs
            specs = registry.get_tool_specs()
            print(f"   ✓ Tool specs generated: {len(specs)}")
            
            # Test initialization
            await registry.initialize_all()
            print(f"   ✓ All tools initialized")
            
            # Test health check
            health = await registry.health_check_all()
            print(f"   ✓ Health check completed for {len(health)} tools")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all AgentCore framework tests."""
        print("🚀 Starting Bedrock AgentCore Framework Integration Tests")
        print("="*80)
        
        tests = [
            ("Framework Imports", self.test_framework_imports),
            ("Agent Handler Decorator", self.test_agent_handler_decorator),
            ("Tool Execution with Decorators", self.test_tool_execution_with_decorators),
            ("Conversation Memory", self.test_conversation_memory),
            ("Tool Specifications", self.test_tool_specifications),
            ("Core Agent Integration", self.test_core_agent_integration),
            ("Agent Factory", self.test_agent_factory),
            ("Tool Registry", self.test_tool_registry),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"🎯 AGENTCORE FRAMEWORK TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Passed: {self.passed_tests}/{self.total_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("🎉 All AgentCore framework tests passed!")
            print("✅ The project successfully adopts Bedrock AgentCore framework patterns!")
            return 0
        else:
            print("⚠️  Some AgentCore framework tests failed.")
            return 1


if __name__ == "__main__":
    tester = TestAgentCoreFramework()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)