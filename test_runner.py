#!/usr/bin/env python3
"""Simple test runner for agent-factory
Tests both agent generation and basic agent functionality
"""

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


class TestResult:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.agent_factory_success = False
        self.agent_factory_error = None
        self.generated_files_exist = False
        self.agent_syntax_valid = False
        self.agent_imports_valid = False
        self.agent_execution_success = False
        self.agent_error = None

    def to_dict(self):
        return {
            "prompt": self.prompt,
            "agent_factory_success": self.agent_factory_success,
            "agent_factory_error": str(self.agent_factory_error) if self.agent_factory_error else None,
            "generated_files_exist": self.generated_files_exist,
            "agent_syntax_valid": self.agent_syntax_valid,
            "agent_imports_valid": self.agent_imports_valid,
            "agent_execution_success": self.agent_execution_success,
            "agent_error": str(self.agent_error) if self.agent_error else None,
        }


class AgentFactoryTester:
    def __init__(self, timeout_seconds: int = 120):
        self.timeout_seconds = timeout_seconds

    def test_agent_factory_generation(self, prompt: str) -> TestResult:
        """Test the agent generation process"""
        result = TestResult(prompt)

        try:
            # Run agent-factory with the prompt
            cmd = [sys.executable, "-m", "src.main", prompt]

            # Start the process
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True
            )

            # Capture output while showing it live
            stdout_lines = []
            stderr_lines = []

            # Read output in real-time
            while True:
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()

                if stdout_line:
                    print(stdout_line.rstrip())  # Show live
                    stdout_lines.append(stdout_line)

                if stderr_line:
                    print(stderr_line.rstrip(), file=sys.stderr)  # Show live
                    stderr_lines.append(stderr_line)

                # Check if process is done
                if process.poll() is not None:
                    break

            # Get any remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                print(remaining_stdout.rstrip())
                stdout_lines.append(remaining_stdout)
            if remaining_stderr:
                print(remaining_stderr.rstrip(), file=sys.stderr)
                stderr_lines.append(remaining_stderr)

            # Join captured output
            captured_stdout = "".join(stdout_lines)
            captured_stderr = "".join(stderr_lines)

            if process.returncode == 0:
                result.agent_factory_success = True
            else:
                # Include both stdout and stderr in error reporting
                error_output = []
                if captured_stdout.strip():
                    error_output.append(f"stdout: {captured_stdout.strip()}")
                if captured_stderr.strip():
                    error_output.append(f"stderr: {captured_stderr.strip()}")

                result.agent_factory_error = f"Exit code {process.returncode}: {'; '.join(error_output)}"

        except Exception as e:
            result.agent_factory_error = f"Execution error: {e}"

        return result

    def test_generated_files(self, result: TestResult) -> TestResult:
        """Check if expected files were generated"""
        workflow_dir = Path("generated_workflows/latest")
        expected_files = ["agent.py", "INSTRUCTIONS.md", "requirements.txt"]

        all_exist = all((workflow_dir / file).exists() for file in expected_files)
        result.generated_files_exist = all_exist

        if not all_exist:
            missing = [file for file in expected_files if not (workflow_dir / file).exists()]
            if result.agent_factory_error:
                result.agent_factory_error += f"; Missing files: {missing}"
            else:
                result.agent_factory_error = f"Missing files: {missing}"

        return result

    def test_agent_syntax(self, result: TestResult, agent_file: Path) -> TestResult:
        """Test if the generated agent has valid Python syntax"""
        try:
            source_code = agent_file.read_text(encoding="utf-8")

            # Parse the AST to check syntax
            ast.parse(source_code)
            result.agent_syntax_valid = True

        except SyntaxError as e:
            result.agent_error = f"Syntax error: {e}"
        except Exception as e:
            result.agent_error = f"File reading error: {e}"

        return result

    def test_agent_imports(self, result: TestResult, agent_file: Path) -> TestResult:
        """Test if the agent imports work without executing main logic"""
        try:
            # Create a temporary module to test imports
            spec = importlib.util.spec_from_file_location("test_agent", agent_file)
            if spec is None or spec.loader is None:
                result.agent_error = "Could not create module spec"
                return result

            # Try to load the module (this will execute imports)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result.agent_imports_valid = True

        except ImportError as e:
            result.agent_error = f"Import error: {e}"
        except Exception as e:
            result.agent_error = f"Module loading error: {e}"

        return result

    def test_agent_basic_execution(self, result: TestResult) -> TestResult:
        """Test if the agent can start without immediate crash"""
        try:
            agent_file = Path("generated_workflows/latest/agent.py")

            # Try to run the agent with a simple argument to see if it starts
            cmd = [sys.executable, str(agent_file), "--help"]
            process = subprocess.run(
                cmd,
                timeout=30,  # Short timeout for basic execution test
                capture_output=True,
                text=True,
            )

            # We don't require success (agent might not support --help)
            # Just that it doesn't crash immediately with import/syntax errors
            if "ImportError" not in process.stderr and "SyntaxError" not in process.stderr:
                result.agent_execution_success = True
            else:
                result.agent_error = f"Execution error: {process.stderr}"

        except subprocess.TimeoutExpired:
            # Timeout might be okay - means the agent started and didn't crash immediately
            result.agent_execution_success = True
        except Exception as e:
            result.agent_error = f"Basic execution test error: {e}"

        return result

    def run_single_test(self, prompt: str) -> TestResult:
        """Run a complete test for a single prompt"""
        # Test agent generation
        result = self.test_agent_factory_generation(prompt)

        # Only proceed with further tests if generation succeeded
        if result.agent_factory_success:
            result = self.test_generated_files(result)

            if result.generated_files_exist:
                agent_file = Path("generated_workflows/latest/agent.py")
                result = self.test_agent_syntax(result, agent_file)

                if result.agent_syntax_valid:
                    result = self.test_agent_imports(result, agent_file)

                    if result.agent_imports_valid:
                        result = self.test_agent_basic_execution(result)

        return result

    def run_tests(self, prompts: list[str]) -> list[TestResult]:
        """Run tests for multiple prompts"""
        results = []

        for i, prompt in enumerate(prompts):
            print(f"\nTesting prompt {i + 1}/{len(prompts)}: {prompt[:50]}...")
            print("-" * 60)

            result = self.run_single_test(prompt)
            results.append(result)

            # Print immediate feedback
            status = "✓" if self.is_success(result) else "✗"
            print(f"\n  {status} Result: {self.get_summary(result)}")

        return results

    def is_success(self, result: TestResult) -> bool:
        """Check if a test result represents complete success"""
        return (
            result.agent_factory_success
            and result.generated_files_exist
            and result.agent_syntax_valid
            and result.agent_imports_valid
            and result.agent_execution_success
        )

    def get_summary(self, result: TestResult) -> str:
        """Get a brief summary of test result"""
        if self.is_success(result):
            return "All tests passed"

        issues = []
        if not result.agent_factory_success:
            issues.append("generation failed")
        elif not result.generated_files_exist:
            issues.append("missing files")
        elif not result.agent_syntax_valid:
            issues.append("syntax error")
        elif not result.agent_imports_valid:
            issues.append("import error")
        elif not result.agent_execution_success:
            issues.append("execution error")

        return f"Failed: {', '.join(issues)}"

    def print_detailed_results(self, results: list[TestResult]):
        """Print detailed results"""
        print("\n" + "=" * 80)
        print("DETAILED TEST RESULTS")
        print("=" * 80)

        total_tests = len(results)
        successful_tests = sum(1 for r in results if self.is_success(r))

        print(f"Overall: {successful_tests}/{total_tests} tests passed\n")

        for i, result in enumerate(results):
            print(f"Test {i + 1}: {result.prompt[:60]}...")
            print(f"  Status: {'PASS' if self.is_success(result) else 'FAIL'}")

            if result.agent_factory_error:
                print(f"  Generation Error: {result.agent_factory_error}")
            if result.agent_error:
                print(f"  Agent Error: {result.agent_error}")

            print(
                f"  Details: Factory={result.agent_factory_success}, "
                f"Files={result.generated_files_exist}, "
                f"Syntax={result.agent_syntax_valid}, "
                f"Imports={result.agent_imports_valid}, "
                f"Execution={result.agent_execution_success}"
            )
            print()


def main():
    """Example usage"""
    # Example prompts
    test_prompts = [
        "Summarize text content from a given webpage URL",
    ]

    tester = AgentFactoryTester(timeout_seconds=120)
    results = tester.run_tests(test_prompts)
    tester.print_detailed_results(results)

    # Optionally save results to JSON
    output_file = Path("test_results.json")
    output_file.write_text(json.dumps([r.to_dict() for r in results], indent=2))
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
