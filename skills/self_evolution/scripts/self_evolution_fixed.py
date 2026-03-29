#!/usr/bin/env python3
"""Fixed version of self_evolution with better git handling."""

import datetime
import hashlib
import json
import logging
import os
import re
import subprocess
import sys

# Add scripts directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration paths relative to Eva's root-mapping
EVA_ROOT = '/tmp/eva'
TASKS_FILE = os.path.join(EVA_ROOT, 'tasks.json')
LOG_FILE = os.path.join(EVA_ROOT, 'self_evolution_fixed.log')

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)


class EvolverFixed:
    """Improved Evolver with better git handling."""

    def __init__(self):
        """Initialize the Evolver and ensure the persistent directory exists."""
        if not os.path.exists(EVA_ROOT):
            os.makedirs(EVA_ROOT)
        self.tasks = self._load_tasks()
        self.repo_path = '/ros2_ws/src/bob_central'

        # Try to import LLM integration
        try:
            from llm_integration import get_llm_integration
            self.llm_integration = get_llm_integration()
            self.has_llm = True
            logging.info('LLM integration available for mutations')
        except ImportError as e:
            logging.warning(f'LLM integration not available: {e}')
            self.llm_integration = None
            self.has_llm = False

    def _load_tasks(self):
        """Load tasks from the JSON file or initialize it."""
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f'Failed to load tasks: {e}')
                return {'active_task': None, 'tasks': {}}
        return {'active_task': None, 'tasks': {}}

    def _save_tasks(self):
        """Save tasks to the persistent JSON file."""
        try:
            with open(TASKS_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            logging.error(f'Failed to save tasks: {e}')

    def _git_reset_if_staged(self, filepath):
        """Reset a file if it is already staged."""
        try:
            # Check if file is staged
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.stdout.strip():
                # File is staged, unstage it
                subprocess.run(
                    ['git', 'reset', 'HEAD', filepath],
                    cwd=self.repo_path,
                    check=True
                )
                logging.info(f'Unstaged previously staged file: {filepath}')
        except Exception as e:
            logging.warning(f'Could not check git staging status: {e}')

    def init_task(self, task_id, description, target_file, test_cmd):
        """Set up a new evolution task."""
        if task_id in self.tasks['tasks']:
            return {'status': 'error', 'message': f'Task {task_id} already exists.'}

        logging.info(f'Initializing task: {task_id} - {description}')

        # Git preparations (on host/container repo)
        try:
            # Create a branch for the task
            subprocess.run(['git', 'checkout', 'main'], cwd=self.repo_path, check=True)
            subprocess.run(
                ['git', 'checkout', '-b', f'evolution/{task_id}'],
                cwd=self.repo_path,
                check=True
            )
            logging.info(f'Created branch evolution/{task_id}')
        except Exception as e:
            return {'status': 'error', 'message': f'Git preparation failed: {e}'}

        self.tasks['tasks'][task_id] = {
            'id': task_id,
            'description': description,
            'target_file': target_file,
            'test_cmd': test_cmd,
            'status': 'initialized',
            'created_at': datetime.datetime.now().isoformat(),
            'iterations': [],
            'best_score': 0,
            'best_iteration': -1
        }
        self.tasks['active_task'] = task_id
        self._save_tasks()
        return {'status': 'success', 'task_id': task_id}

    def _call_llm_for_mutation(self, prompt, current_code, context=None):
        """Call Eva's LLM to generate a code mutation based on the prompt."""
        logging.info(f'LLM mutation requested with prompt: {prompt[:100]}...')

        if self.has_llm and self.llm_integration:
            try:
                # Use real LLM integration
                mutated_code = self.llm_integration.generate_code_mutation(
                    prompt=prompt,
                    current_code=current_code,
                    context=json.dumps(context, indent=2) if context else None,
                    timeout=30  # 30 second timeout for LLM
                )

                if mutated_code:
                    logging.info('LLM mutation generated successfully')
                    return mutated_code
                else:
                    logging.warning('LLM returned no response, using fallback')

            except Exception as e:
                logging.error(f'LLM integration failed: {e}')

        # Fallback: simple mutation logic
        return self._fallback_mutation(prompt, current_code, context)

    def _fallback_mutation(self, prompt, current_code, context):
        """Fallback mutation logic when LLM is not available."""
        prompt_lower = prompt.lower()

        # Simple rule-based mutations
        lines = current_code.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            # Check if this is the calculate_sum function
            if 'def calculate_sum' in line and 'performance' in prompt_lower:
                # Replace with optimized version
                modified_lines.append('def calculate_sum(numbers):')
                modified_lines.append('    """Calculate sum using sum()."""')
                modified_lines.append('    return sum(numbers)')
                # Skip the original implementation
                j = i + 1
                while j < len(lines) and (lines[j].startswith(' ') or lines[j] == ''):
                    j += 1
                return '\n'.join(modified_lines + lines[j:])
            else:
                modified_lines.append(line)

        result = '\n'.join(modified_lines)

        # Add optimization comment if performance mentioned
        if 'performance' in prompt_lower or 'optimize' in prompt_lower:
            result += '\n\n# Performance optimization applied based on mutation prompt'

        return result

    def _apply_mutation(self, task_id, mutation_prompt):
        """Apply LLM-generated mutation to the target file."""
        task = self.tasks['tasks'].get(task_id)
        if not task:
            return {'status': 'error', 'message': f'Task {task_id} not found.'}

        target_file = task['target_file']
        if not os.path.exists(target_file):
            return {'status': 'error', 'message': f'Target file {target_file} not found.'}

        try:
            # Read current code
            with open(target_file, 'r') as f:
                current_code = f.read()

            # Get context about the task
            context = {
                'task_description': task['description'],
                'test_command': task['test_cmd'],
                'previous_iterations': len(task['iterations']),
                'best_score': task.get('best_score', 0),
                'iteration_count': len(task['iterations']) + 1
            }

            # Call LLM for mutation
            mutated_code = self._call_llm_for_mutation(
                mutation_prompt,
                current_code,
                context
            )

            # Extract code from LLM response (handle code blocks)
            code_pattern = r'```(?:python)?\n(.*?)\n```'
            matches = re.findall(code_pattern, mutated_code, re.DOTALL)

            if matches:
                mutated_code = matches[0]
            else:
                # If no code blocks found, use the whole response
                mutated_code = mutated_code.strip()

            # Backup original file
            backup_file = target_file + '.backup'
            with open(backup_file, 'w') as f:
                f.write(current_code)

            # Reset git staging for this file
            self._git_reset_if_staged(target_file)

            # Write mutated code
            with open(target_file, 'w') as f:
                f.write(mutated_code)

            logging.info(f'Applied mutation to {target_file}')

            # Git commit the change
            subprocess.run(
                ['git', 'add', target_file],
                cwd=self.repo_path,
                check=True
            )

            commit_msg = f'Evolution iteration {len(task["iterations"]) + 1}: {mutation_prompt[:50]}...'
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                check=True
            )

            return {
                'status': 'success',
                'message': 'Mutation applied and committed',
                'backup_file': backup_file,
                'original_hash': self._get_file_hash(backup_file),
                'mutated_hash': self._get_file_hash(target_file),
                'llm_used': self.has_llm
            }

        except Exception as e:
            logging.error(f'Mutation failed: {e}')
            return {'status': 'error', 'message': f'Mutation failed: {e}'}

    def _get_file_hash(self, filepath):
        """Get a simple hash of file content for comparison."""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]

    def _run_test_and_score(self, task_id):
        """Run the test command and calculate a score."""
        task = self.tasks['tasks'].get(task_id)
        if not task:
            return {'status': 'error', 'message': f'Task {task_id} not found.', 'score': 0}

        try:
            result = subprocess.run(
                task['test_cmd'],
                shell=True,
                cwd='/ros2_ws',
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            # Calculate score based on test results
            success = (result.returncode == 0)
            score = 100 if success else 0

            return {
                'status': 'success',
                'success': success,
                'score': score,
                'returncode': result.returncode,
                'stdout': result.stdout[-1000:],  # Last 1000 chars
                'stderr': result.stderr[-1000:],
                'timed_out': False
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'success': False,
                'score': 0,
                'message': 'Test timed out',
                'timed_out': True
            }
        except Exception as e:
            return {
                'status': 'error',
                'success': False,
                'score': 0,
                'message': f'Test execution failed: {e}',
                'timed_out': False
            }

    def run_iteration(self, task_id, mutation_prompt=None):
        """Execute one verify-test-learn cycle with LLMnd mutation."""
        task = self.tasks['tasks'].get(task_id)
        if not task:
            return {'status': 'error', 'message': f'Task {task_id} not found.'}

        logging.info(f'Starting iteration for task: {task_id}')

        iteration_result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'mutation_prompt': mutation_prompt,
            'applied': False,
            'test_result': None,
            'score': 0,
            'improvement': False,
            'llm_used': self.has_llm
        }

        try:
            # Step 1: Apply mutation if prompt provided
            if mutation_prompt:
                mutation_result = self._apply_mutation(task_id, mutation_prompt)
                if mutation_result['status'] == 'success':
                    iteration_result['applied'] = True
                    iteration_result['mutation_result'] = mutation_result
                    iteration_result['llm_used'] = mutation_result.get('llm_used', False)
                else:
                    iteration_result['mutation_error'] = mutation_result['message']

            # Step 2: Run test and get score
            test_result = self._run_test_and_score(task_id)
            iteration_result['test_result'] = test_result
            iteration_result['score'] = test_result.get('score', 0)

            # Step 3: Check for improvement
            current_score = iteration_result['score']
            best_score = task.get('best_score', 0)

            if current_score > best_score:
                task['best_score'] = current_score
                task['best_iteration'] = len(task['iterations'])
                iteration_result['improvement'] = True
                logging.info(f'New best score: {current_score} (previous: {best_score})')

                # Push to Gitea if significant improvement
                if current_score >= 80:
                    try:
                        subprocess.run(
                            ['git', 'push', 'sandbox', f'evolution/{task_id}'],
                            cwd=self.repo_path,
                            check=True
                        )
                        iteration_result['pushed_to_gitea'] = True
                    except Exception as e:
                        iteration_result['push_error'] = str(e)

            # Step 4: Record iteration
            task['iterations'].append(iteration_result)
            task['status'] = 'in_progress'
            self._save_tasks()

            return {
                'status': 'success',
                'iteration': iteration_result,
                'current_score': current_score,
                'best_score': task['best_score'],
                'improvement': iteration_result['improvement'],
                'llm_used': iteration_result['llm_used']
            }

        except Exception as e:
            error_msg = f'Iteration failed: {e}'
            logging.error(error_msg)
            iteration_result['error'] = error_msg
            task['iterations'].append(iteration_result)
            self._save_tasks()
            return {'status': 'error', 'message': error_msg}


if __name__ == '__main__':
    evolver = EvolverFixed()

    # Enhanced CLI with mutation support
    if len(sys.argv) > 1:
        action = sys.argv[1]

        if action == 'init' and len(sys.argv) == 6:
            res = evolver.init_task(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
            print(json.dumps(res, indent=2))

        elif action == 'iterate':
            if len(sys.argv) == 3:
                # Iterate without mutation prompt
                res = evolver.run_iteration(sys.argv[2])
                print(json.dumps(res, indent=2))
            elif len(sys.argv) == 4:
                # Iterate with mutation prompt
                res = evolver.run_iteration(sys.argv[2], sys.argv[3])
                print(json.dumps(res, indent=2))

        elif action == 'status':
            if len(sys.argv) == 3:
                # Specific task status
                # res = evolver.get_task_status(sys.argv[2])
                print(json.dumps(evolver.tasks['tasks'].get(sys.argv[2]), indent=2))
            else:
                # Overall status
                print(json.dumps(evolver.tasks, indent=2))

        elif action == 'mutate' and len(sys.argv) == 4:
            # Direct mutation without iteration
            res = evolver._apply_mutation(sys.argv[2], sys.argv[3])
            print(json.dumps(res, indent=2))

        else:
            print('''Self Evolution CLI Usage:
  init <task_id> <description> <target_file> <test_cmd>
  iterate <task_id> [mutation_prompt]
  status [task_id]
  mutate <task_id> <mutation_prompt>''')