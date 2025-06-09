#!/usr/bin/env python3
"""Simple test runner for agent-factory
Tests both agent generation and basic agent functionality
"""

import argparse
import ast
import importlib.util
import json
import subprocess
import sys
from datetime import datetime
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
        self.agent_directory = None

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
            "agent_directory": self.agent_directory,
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

            print(f"Running: {' '.join(cmd)}")
            print("Waiting for agent generation to complete...")

            process = subprocess.run(
                cmd,
                timeout=self.timeout_seconds,
                capture_output=True,
                text=True,
            )

            if process.returncode == 0:
                result.agent_factory_success = True
                print("✅ Agent generation completed successfully")
            else:
                # Include both stdout and stderr in error reporting
                error_output = []
                if process.stdout.strip():
                    error_output.append(f"stdout: {process.stdout.strip()}")
                if process.stderr.strip():
                    error_output.append(f"stderr: {process.stderr.strip()}")

                result.agent_factory_error = f"Exit code {process.returncode}: {'; '.join(error_output)}"
                print(f"❌ Agent generation failed with exit code {process.returncode}")

        except subprocess.TimeoutExpired:
            result.agent_factory_error = f"Timeout after {self.timeout_seconds} seconds - process was terminated"
            print(f"⏰ Agent generation timed out after {self.timeout_seconds} seconds")
        except Exception as e:
            result.agent_factory_error = f"Execution error: {e}"
            print(f"❌ Agent generation error: {e}")

        return result

    def test_generated_files(self, result: TestResult) -> TestResult:
        """Check if expected files were generated"""
        workflow_dir = Path("generated_workflows/latest")
        expected_files = ["agent.py", "INSTRUCTIONS.md", "requirements.txt"]

        print(f"   📋 Checking for files in {workflow_dir}")

        existing_files = []
        missing_files = []

        for file in expected_files:
            if (workflow_dir / file).exists():
                existing_files.append(file)
                print(f"   ✅ Found: {file}")
            else:
                missing_files.append(file)
                print(f"   ❌ Missing: {file}")

        all_exist = len(missing_files) == 0
        result.generated_files_exist = all_exist

        if not all_exist:
            if result.agent_factory_error:
                result.agent_factory_error += f"; Missing files: {missing_files}"
            else:
                result.agent_factory_error = f"Missing files: {missing_files}"

        return result

    def get_most_recent_archive_directory(self) -> str | None:
        """Find the most recent archive directory"""
        archive_dir = Path("generated_workflows/archive")
        if not archive_dir.exists():
            return None

        # Find all archive directories
        archive_dirs = [d for d in archive_dir.iterdir() if d.is_dir()]

        if not archive_dirs:
            return None

        # Sort by modification time and get the most recent
        most_recent = max(archive_dirs, key=lambda d: d.stat().st_mtime)

        return str(most_recent)

    def test_agent_syntax(self, result: TestResult, agent_file: Path) -> TestResult:
        """Test if the generated agent has valid Python syntax"""
        try:
            print(f"   📄 Reading agent file: {agent_file}")
            source_code = agent_file.read_text(encoding="utf-8")
            print(f"   📏 File size: {len(source_code)} characters")

            # Parse the AST to check syntax
            ast.parse(source_code)
            result.agent_syntax_valid = True
            print("   ✅ Syntax validation passed")

        except SyntaxError as e:
            result.agent_error = f"Syntax error: {e}"
            print(f"   ❌ Syntax error: {e}")
        except Exception as e:
            result.agent_error = f"File reading error: {e}"
            print(f"   ❌ File reading error: {e}")

        return result

    def test_agent_imports(self, result: TestResult, agent_file: Path) -> TestResult:
        """Test if the agent imports work without executing main logic"""
        try:
            print(f"   🔄 Creating module spec for {agent_file.name}")
            # Create a temporary module to test imports
            spec = importlib.util.spec_from_file_location("test_agent", agent_file)
            if spec is None or spec.loader is None:
                result.agent_error = "Could not create module spec"
                print("   ❌ Failed to create module spec")
                return result

            print("   📥 Loading module and testing imports...")
            # Try to load the module (this will execute imports)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result.agent_imports_valid = True
            print("   ✅ Import validation passed")

        except ImportError as e:
            result.agent_error = f"Import error: {e}"
            print(f"   ❌ Import error: {e}")
        except Exception as e:
            result.agent_error = f"Module loading error: {e}"
            print(f"   ❌ Module loading error: {e}")

        return result

    def test_agent_basic_execution(self, result: TestResult) -> TestResult:
        """Test if the agent can start without immediate crash"""
        try:
            agent_file = Path("generated_workflows/latest/agent.py")
            print(f"   🏃 Attempting to run agent with --help: {agent_file}")

            # Try to run the agent with a simple argument to see if it starts
            cmd = [sys.executable, str(agent_file), "--help"]
            process = subprocess.run(
                cmd,
                timeout=30,  # Short timeout for basic execution test
                capture_output=True,
                text=True,
            )

            print(f"   📤 Agent process exit code: {process.returncode}")

            # We don't require success (agent might not support --help)
            # Just that it doesn't crash immediately with import/syntax errors
            if "ImportError" not in process.stderr and "SyntaxError" not in process.stderr:
                result.agent_execution_success = True
                print("   ✅ Basic execution test passed")
            else:
                result.agent_error = f"Execution error: {process.stderr}"
                print("   ❌ Execution failed: Import/Syntax error detected")

        except subprocess.TimeoutExpired:
            # For basic execution, timeout likely means it's waiting for input or hanging
            result.agent_error = "Timeout after 30 seconds - agent may be waiting for input or hanging"
            print("   ⏰ Agent execution timed out (30s) - likely waiting for input")
        except Exception as e:
            result.agent_error = f"Basic execution test error: {e}"
            print(f"   ❌ Basic execution test error: {e}")

        return result

    def run_single_test(self, prompt: str) -> TestResult:
        """Run a complete test for a single prompt"""
        print("🔧 Starting agent generation...")

        # Test agent generation
        result = self.test_agent_factory_generation(prompt)

        # Only proceed with further tests if generation succeeded
        if result.agent_factory_success:
            print("📁 Checking generated files...")
            result = self.test_generated_files(result)

            if result.generated_files_exist:
                print("🔍 Validating agent syntax...")
                agent_file = Path("generated_workflows/latest/agent.py")
                result = self.test_agent_syntax(result, agent_file)

                if result.agent_syntax_valid:
                    print("📦 Testing agent imports...")
                    result = self.test_agent_imports(result, agent_file)

                    if result.agent_imports_valid:
                        print("🚀 Testing basic agent execution...")
                        result = self.test_agent_basic_execution(result)

                print("📂 Finding archived agent directory...")
                # Find the archived directory path
                result.agent_directory = self.get_most_recent_archive_directory()
                if result.agent_directory:
                    print(f"   📍 Archived at: {result.agent_directory}")
                else:
                    print("   ⚠️  No archive directory found")
        else:
            print("❌ Agent generation failed, skipping subsequent tests")

        return result

    def run_tests(self, prompts: list[str]) -> list[TestResult]:
        """Run tests for multiple prompts"""
        results = []

        print(f"\n🚀 Starting test run with {len(prompts)} prompts")
        print("=" * 80)

        for i, prompt in enumerate(prompts):
            print(f"\n📋 Test {i + 1}/{len(prompts)}")
            print(f"Prompt: {prompt}")
            print("-" * 60)

            result = self.run_single_test(prompt)
            results.append(result)

            # Print immediate feedback
            status = "✅" if self.is_success(result) else "❌"
            print(f"\n{status} Test {i + 1} Result: {self.get_summary(result)}")

            if not self.is_success(result):
                # Show brief error info for failed tests
                if result.agent_factory_error:
                    print(f"   💥 Generation Error: {result.agent_factory_error[:100]}...")
                if result.agent_error:
                    print(f"   🐛 Agent Error: {result.agent_error[:100]}...")

        print(f"\n🏁 Test run completed! {len(results)} tests finished")
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


def load_prompts_from_file(file_path: str) -> list[str]:
    """Load prompts from a file (one per line or JSON format)"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompts file not found: {file_path}")

    content = path.read_text(encoding="utf-8").strip()

    # Try to parse as JSON first
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [str(item) for item in data]
        else:
            raise ValueError("JSON content must be a list of prompts")
    except json.JSONDecodeError:
        # Fall back to line-by-line parsing
        prompts = [line.strip() for line in content.splitlines() if line.strip()]
        if not prompts:
            raise ValueError("No prompts found in file") from None
        return prompts


def main():
    """Main function with argparse support"""
    parser = argparse.ArgumentParser(
        description="Test runner for agent-factory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single prompt once
  python test_runner.py --prompt "Summarize text from a webpage"

  # Test a single prompt multiple times
  python test_runner.py --prompt "Summarize text from a webpage" --repeat 5

  # Test multiple prompts from command line
  python test_runner.py --prompts "Prompt 1" "Prompt 2" "Prompt 3"

  # Test prompts from a file (one per line)
  python test_runner.py --prompts-file prompts.txt

  # Test prompts from a JSON file
  python test_runner.py --prompts-file prompts.json

  # Adjust timeout for slow generations
  python test_runner.py --prompt "Complex prompt" --timeout 300
        """,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--prompt", type=str, help="Single prompt to test")
    input_group.add_argument("--prompts", nargs="+", type=str, help="Multiple prompts to test (space-separated)")
    input_group.add_argument("--prompts-file", type=str, help="File containing prompts (one per line or JSON array)")

    # Additional options
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat each prompt (default: 1)")
    parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout in seconds for agent generation (default: 120)"
    )
    parser.add_argument(
        "--output-file", type=str, help="Custom output file for test results (default: auto-generated timestamp)"
    )

    args = parser.parse_args()

    # Determine the list of prompts
    if args.prompt:
        prompts = [args.prompt] * args.repeat
    elif args.prompts:
        prompts = args.prompts * args.repeat
    elif args.prompts_file:
        try:
            base_prompts = load_prompts_from_file(args.prompts_file)
            prompts = base_prompts * args.repeat
        except Exception as e:
            print(f"Error loading prompts from file: {e}")
            sys.exit(1)

    # Validate inputs
    if not prompts:
        print("Error: No prompts provided")
        sys.exit(1)

    if args.timeout <= 0:
        print("Error: Timeout must be a positive integer")
        sys.exit(1)

    # Show configuration
    print("Configuration:")
    print(f"  Total prompts: {len(prompts)}")
    print(f"  Unique prompts: {len(set(prompts))}")
    print(f"  Timeout: {args.timeout} seconds")
    print(f"  Repeat factor: {args.repeat}")

    # Run tests
    tester = AgentFactoryTester(timeout_seconds=args.timeout)
    results = tester.run_tests(prompts)
    tester.print_detailed_results(results)

    # Save results
    test_results_dir = Path("test_results")
    test_results_dir.mkdir(exist_ok=True)

    if args.output_file:
        output_file = Path(args.output_file)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = test_results_dir / f"{timestamp}.json"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(json.dumps([r.to_dict() for r in results], indent=2))
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
