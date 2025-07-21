#!/usr/bin/env python3

import urllib.request
import urllib.error
import subprocess
import sys
import os
import re
from datetime import datetime, timedelta


def one_week_ago():
    """Return date string from one week ago in YYYY-MM-DD format."""
    one_week_back = datetime.now() - timedelta(days=7)
    return one_week_back.strftime("%Y-%m-%d")


FUNCTION_MAPPING = {
    'one_week_ago': one_week_ago,
}


def replace_url_placeholders(url):
    """Replace {function_name} placeholders in URL with function call results."""
    def replacer(match):
        func_name = match.group(1)
        if func_name in FUNCTION_MAPPING:
            return str(FUNCTION_MAPPING[func_name]())
        return match.group(0)  # Return original if function not found
    
    return re.sub(r'\{([^}]+)\}', replacer, url)


def read_url_mapping(mapping_file):
    """Read URL to filename mapping from file."""
    url_mapping = {}
    try:
        with open(mapping_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    print(f"Warning: Invalid format at line {line_num}: {line}")
                    continue

                url, filename = parts
                processed_url = replace_url_placeholders(url)
                url_mapping[processed_url] = filename
    except FileNotFoundError:
        print(f"Error: Mapping file '{mapping_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading mapping file: {e}")
        sys.exit(1)

    return url_mapping


def download_file(url, filename):
    """Download file from URL and save to filename."""
    try:
        print(f"Downloading {url} -> {filename}")

        with urllib.request.urlopen(url) as response:
            content = response.read()

        with open(filename, 'wb') as f:
            f.write(content)

        print(f"Successfully downloaded {filename}")
        return True

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} downloading {url}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error downloading {url}: {e.reason}")
        return False


def git_push():
    """Perform git add, commit, and push."""
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        print("Files added to git")

        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True)
        if not result.stdout.strip():
            print("No changes to commit")
            return True

        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        commit_msg = f"download_and_push.py: {timestamp}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        print("Changes committed")

        subprocess.run(['git', 'push'], check=True)
        print("Changes pushed to remote")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"Error during git operations: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python download_and_push.py <url_mapping_file>")
        print("Mapping file format: <url> <filename>")
        sys.exit(1)

    mapping_file = sys.argv[1]
    url_mapping = read_url_mapping(mapping_file)

    if not url_mapping:
        print("No valid URL mappings found")
        sys.exit(1)

    success_count = 0
    total_count = len(url_mapping)

    for url, filename in url_mapping.items():
        if download_file(url, filename):
            success_count += 1

    print(f"\nDownload complete: {success_count}/{total_count} files successful")

    if success_count > 0:
        if git_push():
            print("Git push completed successfully")
        else:
            print("Git push failed")
            sys.exit(1)
    else:
        print("No files downloaded, skipping git push")


if __name__ == "__main__":
    main()
