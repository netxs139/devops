import os
import sys


def check_line_limits(directory, limit=300, extensions=(".js", ".css", ".html")):
    """检查指定目录下的文件行数是否超过限制�?""
    errors = []
    for root, _, files in os.walk(directory):
        # 排除外部库或压缩文件
        if any(x in root for x in ["vendor", "lib", "dist", "node_modules"]):
            continue

        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        lines = f.readlines()
                        if len(lines) > limit:
                            errors.append(f"{filepath}: {len(lines)} lines (Limit: {limit})")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    return errors


if __name__ == "__main__":
    print("Checking frontend file line limits (300 line law)...")
    frontend_dir = "devops_portal/static"
    limit_errors = check_line_limits(frontend_dir)

    if limit_errors:
        print("\nFAIL: The following files exceed the 300-line limit:")
        for err in limit_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("SUCCESS: All frontend files are within limits.")
        sys.exit(0)
