#!/usr/bin/env python3
"""
Comprehensive test runner for Ponder application.
Runs both backend and frontend tests with coverage reporting and CI/CD integration.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.results = {
            "backend": {"passed": False, "coverage": 0, "duration": 0},
            "frontend": {"passed": False, "coverage": 0, "duration": 0}
        }
    
    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")
    
    def run_command(self, command: List[str], cwd: Path, timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, and stderr."""
        try:
            self.print_info(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        self.print_header("Checking Dependencies")
        
        dependencies_ok = True
        
        # Check Python and pip
        success, _, _ = self.run_command(["python", "--version"], self.project_root)
        if success:
            self.print_success("Python is available")
        else:
            self.print_error("Python is not available")
            dependencies_ok = False
        
        # Check Node.js and npm
        success, _, _ = self.run_command(["node", "--version"], self.project_root)
        if success:
            self.print_success("Node.js is available")
        else:
            self.print_error("Node.js is not available")
            dependencies_ok = False
        
        success, _, _ = self.run_command(["npm", "--version"], self.project_root)
        if success:
            self.print_success("npm is available")
        else:
            self.print_error("npm is not available")
            dependencies_ok = False
        
        return dependencies_ok
    
    def setup_backend_environment(self) -> bool:
        """Set up backend testing environment."""
        self.print_header("Setting Up Backend Environment")
        
        # Check if virtual environment exists
        venv_path = self.backend_dir / ".venv"
        if not venv_path.exists():
            self.print_info("Creating virtual environment...")
            success, _, stderr = self.run_command(
                ["python", "-m", "venv", ".venv"],
                self.backend_dir
            )
            if not success:
                self.print_error(f"Failed to create virtual environment: {stderr}")
                return False
        
        # Determine activation script based on OS
        if os.name == 'nt':  # Windows
            activate_script = venv_path / "Scripts" / "activate.bat"
            pip_path = venv_path / "Scripts" / "pip"
        else:  # Unix/Linux/macOS
            activate_script = venv_path / "bin" / "activate"
            pip_path = venv_path / "bin" / "pip"
        
        # Install dependencies
        self.print_info("Installing backend dependencies...")
        success, _, stderr = self.run_command(
            [str(pip_path), "install", "-r", "requirements.txt"],
            self.backend_dir
        )
        if not success:
            self.print_error(f"Failed to install backend dependencies: {stderr}")
            return False
        
        self.print_success("Backend environment setup complete")
        return True
    
    def setup_frontend_environment(self) -> bool:
        """Set up frontend testing environment."""
        self.print_header("Setting Up Frontend Environment")
        
        # Check if node_modules exists
        node_modules_path = self.frontend_dir / "node_modules"
        if not node_modules_path.exists():
            self.print_info("Installing frontend dependencies...")
            success, _, stderr = self.run_command(
                ["npm", "install"],
                self.frontend_dir
            )
            if not success:
                self.print_error(f"Failed to install frontend dependencies: {stderr}")
                return False
        else:
            self.print_info("Frontend dependencies already installed")
        
        self.print_success("Frontend environment setup complete")
        return True
    
    def run_backend_tests(self, coverage: bool = True, verbose: bool = False) -> bool:
        """Run backend tests with pytest."""
        self.print_header("Running Backend Tests")
        
        start_time = time.time()
        
        # Determine Python executable in virtual environment
        venv_path = self.backend_dir / ".venv"
        if os.name == 'nt':  # Windows
            python_path = venv_path / "Scripts" / "python"
        else:  # Unix/Linux/macOS
            python_path = venv_path / "bin" / "python"
        
        # Build pytest command
        command = [str(python_path), "-m", "pytest"]
        
        if coverage:
            command.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
                "--cov-report=term-missing"
            ])
        
        if verbose:
            command.append("-v")
        
        command.extend([
            "--tb=short",
            "tests/"
        ])
        
        success, stdout, stderr = self.run_command(command, self.backend_dir, timeout=600)
        
        duration = time.time() - start_time
        self.results["backend"]["duration"] = duration
        
        if success:
            self.print_success(f"Backend tests passed in {duration:.2f}s")
            self.results["backend"]["passed"] = True
            
            # Extract coverage percentage from output
            if coverage and "TOTAL" in stdout:
                try:
                    lines = stdout.split('\n')
                    for line in lines:
                        if "TOTAL" in line:
                            coverage_match = line.split()[-1]
                            if coverage_match.endswith('%'):
                                coverage_percent = int(coverage_match[:-1])
                                self.results["backend"]["coverage"] = coverage_percent
                                self.print_info(f"Backend test coverage: {coverage_percent}%")
                                break
                except:
                    pass
        else:
            self.print_error(f"Backend tests failed: {stderr}")
            if stdout:
                print(stdout)
        
        return success
    
    def run_frontend_tests(self, coverage: bool = True, verbose: bool = False) -> bool:
        """Run frontend tests with Jest."""
        self.print_header("Running Frontend Tests")
        
        start_time = time.time()
        
        # Build npm test command
        command = ["npm", "test"]
        
        # Set environment variables for CI mode
        env = os.environ.copy()
        env["CI"] = "true"  # Prevents Jest from running in watch mode
        
        if coverage:
            env["GENERATE_SOURCEMAP"] = "false"
            command.append("--")
            command.extend([
                "--coverage",
                "--coverageDirectory=coverage",
                "--coverageReporters=html,lcov,text-summary"
            ])
        
        if verbose:
            command.extend(["--verbose"])
        
        command.extend([
            "--watchAll=false",
            "--testTimeout=30000"
        ])
        
        try:
            result = subprocess.run(
                command,
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=600,
                env=env
            )
            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            success = False
            stdout = ""
            stderr = "Frontend tests timed out after 600 seconds"
        
        duration = time.time() - start_time
        self.results["frontend"]["duration"] = duration
        
        if success:
            self.print_success(f"Frontend tests passed in {duration:.2f}s")
            self.results["frontend"]["passed"] = True
            
            # Extract coverage percentage from output
            if coverage and "All files" in stdout:
                try:
                    lines = stdout.split('\n')
                    for line in lines:
                        if "All files" in line and "%" in line:
                            parts = line.split()
                            for part in parts:
                                if part.endswith('%'):
                                    coverage_percent = float(part[:-1])
                                    self.results["frontend"]["coverage"] = coverage_percent
                                    self.print_info(f"Frontend test coverage: {coverage_percent}%")
                                    break
                            break
                except:
                    pass
        else:
            self.print_error(f"Frontend tests failed: {stderr}")
            if stdout:
                print(stdout)
        
        return success
    
    def run_linting(self) -> bool:
        """Run linting for both backend and frontend."""
        self.print_header("Running Code Linting")
        
        linting_passed = True
        
        # Backend linting with flake8 (if available)
        self.print_info("Running backend linting...")
        venv_path = self.backend_dir / ".venv"
        if os.name == 'nt':
            flake8_path = venv_path / "Scripts" / "flake8"
        else:
            flake8_path = venv_path / "bin" / "flake8"
        
        if flake8_path.exists():
            success, _, stderr = self.run_command(
                [str(flake8_path), "app/", "--max-line-length=100", "--ignore=E203,W503"],
                self.backend_dir
            )
            if success:
                self.print_success("Backend linting passed")
            else:
                self.print_warning(f"Backend linting issues found: {stderr}")
                # Don't fail the entire test suite for linting issues
        else:
            self.print_warning("flake8 not available, skipping backend linting")
        
        # Frontend linting with ESLint (if available)
        self.print_info("Running frontend linting...")
        success, _, stderr = self.run_command(
            ["npm", "run", "lint", "--if-present"],
            self.frontend_dir
        )
        if success:
            self.print_success("Frontend linting passed")
        else:
            self.print_warning(f"Frontend linting issues found: {stderr}")
        
        return linting_passed
    
    def generate_report(self, output_file: Optional[str] = None):
        """Generate a comprehensive test report."""
        self.print_header("Test Results Summary")
        
        # Calculate overall results
        all_passed = all(result["passed"] for result in self.results.values())
        total_duration = sum(result["duration"] for result in self.results.values())
        avg_coverage = sum(result["coverage"] for result in self.results.values()) / len(self.results)
        
        # Print summary
        if all_passed:
            self.print_success("All tests passed!")
        else:
            self.print_error("Some tests failed!")
        
        print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}")
        for component, result in self.results.items():
            status = "PASSED" if result["passed"] else "FAILED"
            color = Colors.OKGREEN if result["passed"] else Colors.FAIL
            print(f"  {component.capitalize()}: {color}{status}{Colors.ENDC}")
            print(f"    Duration: {result['duration']:.2f}s")
            print(f"    Coverage: {result['coverage']:.1f}%")
        
        print(f"\n{Colors.BOLD}Overall:{Colors.ENDC}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Average Coverage: {avg_coverage:.1f}%")
        
        # Generate JSON report if requested
        if output_file:
            report_data = {
                "timestamp": time.time(),
                "overall": {
                    "passed": all_passed,
                    "duration": total_duration,
                    "average_coverage": avg_coverage
                },
                "components": self.results
            }
            
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.print_info(f"Detailed report saved to {output_file}")
        
        return all_passed
    
    def run_all_tests(self, coverage: bool = True, verbose: bool = False, 
                     skip_setup: bool = False, components: Optional[List[str]] = None) -> bool:
        """Run all tests with setup and reporting."""
        self.print_header("Ponder Application Test Suite")
        
        # Check dependencies
        if not self.check_dependencies():
            self.print_error("Dependency check failed")
            return False
        
        # Setup environments
        if not skip_setup:
            if not components or "backend" in components:
                if not self.setup_backend_environment():
                    self.print_error("Backend environment setup failed")
                    return False
            
            if not components or "frontend" in components:
                if not self.setup_frontend_environment():
                    self.print_error("Frontend environment setup failed")
                    return False
        
        # Run tests
        success = True
        
        if not components or "backend" in components:
            if not self.run_backend_tests(coverage, verbose):
                success = False
        
        if not components or "frontend" in components:
            if not self.run_frontend_tests(coverage, verbose):
                success = False
        
        # Run linting
        self.run_linting()
        
        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Ponder application tests")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-setup", action="store_true", help="Skip environment setup")
    parser.add_argument("--components", nargs="+", choices=["backend", "frontend"], 
                       help="Run tests for specific components only")
    parser.add_argument("--report", help="Generate JSON report file")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit with error code on failure)")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests(
            coverage=not args.no_coverage,
            verbose=args.verbose,
            skip_setup=args.skip_setup,
            components=args.components
        )
        
        # Generate report
        overall_success = runner.generate_report(args.report)
        
        if args.ci and not overall_success:
            sys.exit(1)
        
        return overall_success
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()