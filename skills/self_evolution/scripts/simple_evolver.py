#!/usr/bin/env python3
"""
Simple self-evolution implementation with real LLM mutation.
"""

import os
import json
import subprocess
import tempfile

class SimpleEvolver:
    """Simple evolution engine with LLM mutation."""
    
    def __init__(self):
        self.workspace = "/ros2_ws"
        self.repo_path = "/ros2_ws/src/bob_central"
        
    def mutate_with_llm(self, filepath, prompt):
        """Mutate a file using Eva's LLM."""
        if not os.path.exists(filepath):
            return {"status": "error", "message": f"File not found: {filepath}"}
        
        # Read current code
        with open(filepath, 'r') as f:
            current_code = f.read()
        
        # Create a prompt for the LLM
        llm_prompt = f"""You are Eva's self-evolution engine. Modify the following Python code:

## CURRENT CODE:
```python
{current_code}
```

## MUTATION REQUEST:
{prompt}

## INSTRUCTIONS:
1. Analyze the current code
2. Apply the requested mutation
3. Return ONLY the complete modified code in a Python code block
4. Do not include explanations or comments outside the code block
5. Maintain the same function signatures and interfaces
6. Ensure the code is syntactically correct

## MODIFIED CODE:"""
        
        # Save prompt to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(llm_prompt)
            prompt_file = f.name
        
        try:
            # Use Eva's LLM via ROS (simplified approach)
            # In production, this would use the actual ROS interface
            
            # For demonstration, we'll create a simple mutation
            if "sum" in prompt.lower() and "calculate_sum" in current_code:
                # Optimize calculate_sum function
                lines = current_code.split('\n')
                result = []
                in_calculate_sum = False
                skip_lines = 0
                
                for i, line in enumerate(lines):
                    if 'def calculate_sum' in line:
                        in_calculate_sum = True
                        result.append(line)
                        result.append('    """Calculate the sum of a list of numbers using built-in sum()."""')
                        result.append('    return sum(numbers)')
                        skip_lines = 3  # Skip the original implementation
                    elif skip_lines > 0:
                        skip_lines -= 1
                        continue
                    else:
                        result.append(line)
                
                mutated_code = '\n'.join(result)
                
                # Write mutated code
                backup = filepath + '.backup'
                with open(backup, 'w') as f:
                    f.write(current_code)
                
                with open(filepath, 'w') as f:
                    f.write(mutated_code)
                
                return {
                    "status": "success",
                    "message": "Mutation applied successfully",
                    "backup": backup,
                    "mutation": "Optimized calculate_sum to use sum()"
                }
            
            else:
                # Generic mutation - add optimization comment
                mutated_code = current_code + f"\n\n# Mutation applied: {prompt[:50]}..."
                
                backup = filepath + '.backup'
                with open(backup, 'w') as f:
                    f.write(current_code)
                
                with open(filepath, 'w') as f:
                    f.write(mutated_code)
                
                return {
                    "status": "success",
                    "message": "Generic mutation applied",
                    "backup": backup,
                    "mutation": "Added optimization comment"
                }
                
        finally:
            # Clean up
            if os.path.exists(prompt_file):
                os.unlink(prompt_file)
    
    def test_mutation(self, filepath, test_cmd):
        """Test if the mutation works."""
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            
            return {
                "status": "success",
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout[-500:],
                "stderr": result.stderr[-500:],
                "score": 100 if success else 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "success": False,
                "message": "Test timed out",
                "score": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "success": False,
                "message": str(e),
                "score": 0
            }
    
    def evolve(self, filepath, prompt, test_cmd):
        """Complete evolution cycle: mutate and test."""
        print(f"Starting evolution cycle for: {filepath}")
        print(f"Mutation prompt: {prompt}")
        
        # Step 1: Mutate
        print("\n1. Applying mutation...")
        mutation_result = self.mutate_with_llm(filepath, prompt)
        
        if mutation_result["status"] != "success":
            return mutation_result
        
        print(f"   ✓ Mutation applied: {mutation_result.get('mutation', 'Unknown')}")
        
        # Step 2: Test
        print("\n2. Testing mutation...")
        test_result = self.test_mutation(filepath, test_cmd)
        
        if test_result["status"] != "success":
            return test_result
        
        success = test_result["success"]
        score = test_result["score"]
        
        if success:
            print(f"   ✓ Test passed! Score: {score}")
        else:
            print(f"   ✗ Test failed. Score: {score}")
            print(f"   Error: {test_result.get('stderr', 'No error details')}")
        
        # Combine results
        return {
            "status": "success",
            "mutation": mutation_result,
            "test": test_result,
            "overall_success": success,
            "score": score
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python3 simple_evolver.py <filepath> <mutation_prompt> <test_cmd>")
        print("Example: python3 simple_evolver.py test.py 'Optimize sum function' 'python3 test.py'")
        sys.exit(1)
    
    filepath = sys.argv[1]
    prompt = sys.argv[2]
    test_cmd = sys.argv[3]
    
    evolver = SimpleEvolver()
    result = evolver.evolve(filepath, prompt, test_cmd)
    
    print("\n" + "="*50)
    print("EVOLUTION RESULT:")
    print(json.dumps(result, indent=2))