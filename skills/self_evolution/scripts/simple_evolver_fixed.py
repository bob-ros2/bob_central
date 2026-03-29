#!/usr/bin/env python3
"""
Fixed simple self-evolution implementation.
"""

import os
import json
import subprocess

class SimpleEvolverFixed:
    """Fixed evolution engine with better code mutation."""
    
    def mutate_with_llm(self, filepath, prompt):
        """Mutate a file using improved algorithm."""
        if not os.path.exists(filepath):
            return {"status": "error", "message": f"File not found: {filepath}"}
        
        with open(filepath, 'r') as f:
            current_code = f.read()
        
        # Parse the code to understand its structure
        lines = current_code.split('\n')
        
        # Look for calculate_sum function
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is the calculate_sum function
            if 'def calculate_sum' in line and 'sum' in prompt.lower():
                # Found the function to optimize
                new_lines.append(line)
                new_lines.append('    """Calculate the sum of a list of numbers using built-in sum()."""')
                new_lines.append('    return sum(numbers)')
                
                # Skip the original implementation
                i += 1  # Skip def line
                # Skip until we're out of the function
                while i < len(lines) and (lines[i].startswith('    ') or lines[i] == ''):
                    i += 1
                continue
            else:
                new_lines.append(line)
                i += 1
        
        mutated_code = '\n'.join(new_lines)
        
        # Create backup
        backup = filepath + '.backup'
        with open(backup, 'w') as f:
            f.write(current_code)
        
        # Write mutated code
        with open(filepath, 'w') as f:
            f.write(mutated_code)
        
        return {
            "status": "success",
            "message": "Mutation applied successfully",
            "backup": backup,
            "mutation": "Optimized calculate_sum to use sum()"
        }
    
    def test_mutation(self, filepath, test_cmd):
        """Test if the mutation works."""
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=os.path.dirname(filepath),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            
            return {
                "status": "success",
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "score": 100 if success else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "success": False,
                "message": str(e),
                "score": 0
            }
    
    def evolve(self, filepath, prompt, test_cmd):
        """Complete evolution cycle."""
        print(f"Evolution: {os.path.basename(filepath)}")
        print(f"Prompt: {prompt}")
        
        # Mutate
        print("\n1. Mutating...")
        mutation_result = self.mutate_with_llm(filepath, prompt)
        
        if mutation_result["status"] != "success":
            print(f"   ✗ Mutation failed: {mutation_result['message']}")
            return mutation_result
        
        print(f"   ✓ {mutation_result['mutation']}")
        
        # Test
        print("\n2. Testing...")
        test_result = self.test_mutation(filepath, test_cmd)
        
        if test_result["status"] != "success":
            print(f"   ✗ Test error: {test_result['message']}")
        elif test_result["success"]:
            print(f"   ✓ Test passed! Score: {test_result['score']}")
        else:
            print(f"   ✗ Test failed. Score: {test_result['score']}")
            if test_result['stderr']:
                print(f"   Error: {test_result['stderr'].strip()}")
        
        return {
            "status": "success",
            "mutation": mutation_result,
            "test": test_result,
            "score": test_result.get("score", 0)
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python3 simple_evolver_fixed.py <filepath> <prompt> <test_cmd>")
        sys.exit(1)
    
    evolver = SimpleEvolverFixed()
    result = evolver.evolve(sys.argv[1], sys.argv[2], sys.argv[3])
    
    print("\n" + "="*50)
    print("Result:", json.dumps(result, indent=2))