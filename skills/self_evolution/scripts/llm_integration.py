#!/usr/bin/env python3
"""LLM Integration for Self-Evolution Skill."""

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading


class LLMIntegration:
    """Handle integration with Eva's LLM system for code mutation."""

    def __init__(self, use_ros=True):
        """Initialize LLM integration."""
        self.use_ros = use_ros
        self.llm_response = None
        self.response_received = threading.Event()

        if use_ros:
            try:
                rclpy.init()
                self.node = Node('self_evolution_llm_client')

                # Create publisher for LLM prompts
                self.prompt_pub = self.node.create_publisher(
                    String,
                    '/eva/user_query',
                    10
                )

                # Create subscriber for LLM responses
                self.response_sub = self.node.create_subscription(
                    String,
                    '/eva/llm_response',
                    self._llm_response_callback,
                    10
                )

                self.ros_thread = threading.Thread(target=self._ros_spin)
                self.ros_thread.daemon = True
                self.ros_thread.start()

                print('LLM Integration: ROS initialized successfully')
            except Exception as e:
                print(f'LLM Integration: ROS initialization failed: {e}')
                self.use_ros = False

    def _llm_response_callback(self, msg):
        """Handle callback for LLM responses."""
        self.llm_response = msg.data
        self.response_received.set()

    def _ros_spin(self):
        """Spin ROS node in background thread."""
        rclpy.spin(self.node)

    def generate_mutation_via_ros(self, prompt, timeout=30):
        """Generate code mutation using ROS LLM interface."""
        if not self.use_ros:
            return None

        self.llm_response = None
        self.response_received.clear()

        # Publish prompt to LLM
        msg = String()
        msg.data = prompt
        self.prompt_pub.publish(msg)

        # Wait for response
        if self.response_received.wait(timeout):
            return self.llm_response
        else:
            print(f'LLM Integration: Timeout after {timeout} seconds')
            return None

    def generate_mutation_via_direct(self, prompt, current_code, context):
        """Generate code mutation using direct LLM call (fallback)."""
        # Create a structured prompt for the LLM
        structured_prompt = f'''You are Eva's self-evolution engine. Your task is to improve the following code based on the mutation prompt.

## CURRENT CODE:
```python
{current_code}
```

## MUTATION PROMPT:
{prompt}

## CONTEXT:
{context}

## INSTRUCTIONS:
1. Analyze the current code and the mutation prompt
2. Generate an improved version of the code
3. Focus on:
   - Fixing bugs or issues mentioned in the prompt
   - Improving performance if requested
   - Adding features if requested
   - Refactoring for better readability/maintainability
4. Return ONLY the complete modified code in a Python code block
5. Do not include explanations, comments about changes, or markdown outside the code block
6. Maintain backward compatibility unless explicitly requested otherwise
7. Ensure the code is syntactically correct and follows Python best practices

## MODIFIED CODE:'''

        # In a real implementation, this would call the actual LLM
        # For now, we'll use a simple placeholder that demonstrates the concept
        return self._placeholder_llm_response(current_code, prompt)

    def _placeholder_llm_response(self, current_code, prompt):
        """Generate placeholder LLM response for demonstration."""
        # This is a simple placeholder - in production, this would call the actual LLM

        # Analyze prompt for common patterns
        prompt_lower = prompt.lower()

        if 'performance' in prompt_lower or 'faster' in prompt_lower:
            # Add performance optimization comment
            return f'''{current_code}

# Performance optimization added based on mutation prompt
# TODO: Implement actual performance improvements here'''

        elif 'bug' in prompt_lower or 'fix' in prompt_lower or 'error' in prompt_lower:
            # Add error handling
            lines = current_code.split('\n')
            enhanced_lines = []
            for line in lines:
                enhanced_lines.append(line)
                # Simple example: add try-except to function definitions
                if line.strip().startswith('def ') and '):' in line:
                    enhanced_lines.append('    try:')
            enhanced_code = '\n'.join(enhanced_lines)
            return f'''{enhanced_code}
        except Exception as e:
            logging.error(f'Error in function: {{e}}')
            raise'''

        elif 'feature' in prompt_lower or 'add' in prompt_lower:
            # Add a placeholder feature
            return f'''{current_code}

# New feature placeholder added
def new_feature():
    """Feature added based on mutation prompt."""
    pass'''

        else:
            # Default: add optimization comment
            return f'''{current_code}

# Code optimized based on mutation prompt: {prompt[:50]}...'''

    def generate_code_mutation(self, prompt, current_code, context=None, timeout=30):
        """Generate a code mutation using available LLM methods."""
        # Try ROS integration first
        if self.use_ros:
            print('LLM Integration: Attempting ROS-based mutation generation...')

            # Create comprehensive prompt for ROS LLM
            ros_prompt = f'''As Eva's self-evolution engine, modify this code:

Current code:
```python
{current_code}
```

Mutation request: {prompt}

Context: {context if context else 'General code improvement'}

Return ONLY the complete modified Python code in a code block, no explanations.'''

            response = self.generate_mutation_via_ros(ros_prompt, timeout)
            if response:
                print('LLM Integration: Received response via ROS')
                return response

        # Fallback to direct method
        print('LLM Integration: Using direct method (ROS unavailable or timed out)')
        return self.generate_mutation_via_direct(prompt, current_code, context)

    def cleanup(self):
        """Clean up resources."""
        if self.use_ros:
            self.node.destroy_node()
            rclpy.shutdown()


# Singleton instance
_llm_integration = None


def get_llm_integration():
    """Get or create LLM integration instance."""
    global _llm_integration
    if _llm_integration is None:
        _llm_integration = LLMIntegration()
    return _llm_integration


if __name__ == '__main__':
    # Test the LLM integration
    llm = get_llm_integration()

    test_code = '''def calculate_sum(numbers):
    result = 0
    for num in numbers:
        result += num
    return result'''

    test_prompt = 'Optimize this function for performance'
    test_context = 'Function calculates sum of numbers'

    result = llm.generate_code_mutation(test_prompt, test_code, test_context)
    print('Generated mutation:')
    print(result)

    llm.cleanup()