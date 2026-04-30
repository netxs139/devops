import argparse
import concurrent.futures
import subprocess
import sys
import time


# 定义 ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def run_command_captured(command, description):
    start_time = time.time()
    try:
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        duration = time.time() - start_time
        success = process.returncode == 0
        return success, process.stdout, duration, description, process.returncode
    except Exception as e:
        duration = time.time() - start_time
        return False, f"ERROR: {str(e)}", duration, description, -1


def execute_stage_parallel(tasks, stage_name):
    print(f"\n{CYAN}>>> Starting {stage_name} (Parallel Execution)...{RESET}")
    all_success = True
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_task = {executor.submit(run_command_captured, cmd, desc): desc for cmd, desc in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            success, output, duration, desc, retcode = future.result()
            results.append((success, output, duration, desc, retcode))
            if not success:
                all_success = False

    # 统一打印结果避免输出交错
    for success, output, duration, desc, retcode in results:
        print(f"\n{YELLOW}--- Output for: {desc} ---{RESET}")
        print(output.strip())
        if success:
            print(f"{GREEN}[V] [{desc}] PASSED ({duration:.1f}s){RESET}")
        else:
            print(f"{RED}[X] [{desc}] FAILED (Exit code: {retcode}){RESET}")

    return all_success


def main():
    if sys.stdout.encoding.lower() != "utf-8":
        try:
            import io

            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="DevOps Platform Full Gate (Pre-merge Check)")
    parser.add_argument("--mode", choices=["fast", "full"], default="full", help="Check mode (fast: skip build, full: all checks)")
    args = parser.parse_args()

    print(f"{YELLOW}====================================================================")
    print(f"        DevOps Platform Full Gate Check - Mode: {args.mode.upper()}        ")
    print(f"===================================================================={RESET}")

    overall_start = time.time()

    # Stage 1: Fast & Core Checks (Parallel)
    stage1_tasks = [
        ("just security-audit", "L1: Security Audit (Secrets, SAST, Deps)"),
        ("just verify", "L2: Total Verification (Lint, Imports, Cov >= 80%)"),
        ("just arch-audit", "L1.5: Architecture & Anti-Pattern Audit"),
    ]

    if not execute_stage_parallel(stage1_tasks, "Stage 1 (Security & Verification)"):
        print(f"\n{RED}>>> Stage 1 FAILED. Gate execution stopped.{RESET}")
        sys.exit(1)

    # Stage 2: Build & Advanced Checks (Parallel)
    if args.mode == "full":
        stage2_tasks = [("just build", "L3: Docker Image Build & Cache Verification"), ("just dbt-build", "L4: dbt Data Model Audit")]
        if not execute_stage_parallel(stage2_tasks, "Stage 2 (Build & Data Audit)"):
            print(f"\n{RED}>>> Stage 2 FAILED. Gate execution stopped.{RESET}")
            sys.exit(1)

    overall_duration = time.time() - overall_start
    print(f"\n{GREEN}====================================================================")
    print(f"        SUCCESS: FULL GATE PASSED ({overall_duration:.1f}s)            ")
    print("        Your code is now ready for merge/deployment.                ")
    print(f"===================================================================={RESET}")


if __name__ == "__main__":
    main()
