#!/usr/bin/env python3
"""
Demo script showing regex pattern search functionality in TarFileReader.
"""

import os
import tempfile
import tarfile
import re
from tar_file_reader import TarFileReader


def create_test_archive():
    """Create a test .tar.gz file with various file types for searching."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = {
            'config/app.conf': 'server_port=8080\ndebug=true\nlog_level=INFO\napi_key=secret123',
            'config/database.ini': '[database]\nhost=localhost\nport=5432\nuser=admin\npassword=admin123',
            'src/main.py': 'import sys\ndef main():\n    print("Hello World")\n    return 0\n\nif __name__ == "__main__":\n    main()',
            'src/utils.py': 'import re\nimport json\n\ndef validate_email(email):\n    pattern = r"^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"\n    return re.match(pattern, email)',
            'data/users.csv': 'id,name,email,password\n1,Alice,alice@example.com,hash123\n2,Bob,bob@test.org,hash456',
            'data/logs.txt': '2024-01-01 10:00:00 INFO Server started\n2024-01-01 10:01:00 ERROR Connection failed\n2024-01-01 10:02:00 DEBUG Retrying connection',
            'docs/README.md': '# Test Project\n\nThis is a test project for demonstration.\n\n## Features\n- Configuration management\n- Database integration',
            'tests/test_main.py': 'import unittest\nfrom src.main import main\n\nclass TestMain(unittest.TestCase):\n    def test_main(self):\n        self.assertEqual(main(), 0)',
            'lib/helper.js': 'function validatePassword(pwd) {\n    const pattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)[A-Za-z\\d@$!%*?&]{8,}$/;\n    return pattern.test(pwd);\n}',
            'static/style.css': 'body { margin: 0; padding: 20px; }\n.header { background-color: #333; color: white; }\n.error { color: red; }'
        }

        # Write test files
        for file_path, content in test_files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Create tar.gz archive
        archive_path = 'test_search.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            for file_path in test_files.keys():
                full_path = os.path.join(temp_dir, file_path)
                tar.add(full_path, arcname=file_path)

        return archive_path


def demo_search_functionality():
    """Demonstrate all search functions."""

    # Create test archive
    archive_path = create_test_archive()
    print(f"Created test archive: {archive_path}")
    print("=" * 60)

    try:
        reader = TarFileReader(archive_path)

        # 1. Search by file path pattern
        print("1. Search files by path pattern (containing 'src/'):")
        for path, name, size in reader.search_files_by_pattern(r'src/'):
            print(f"  {path} ({name}) - {size} bytes")
        print()

        # 2. Search by filename pattern
        print("2. Search files by name pattern (ending with .py):")
        for path, name, size in reader.search_files_by_name_pattern(r'\.py$'):
            print(f"  {path} ({name}) - {size} bytes")
        print()

        # 3. Search by file extension
        print("3. Search files by extension (.conf files):")
        for path, name, size in reader.search_files_by_extension('conf'):
            print(f"  {path} ({name}) - {size} bytes")
        print()

        # 4. Search content by pattern
        print("4. Search content containing 'password' or 'secret':")
        pattern = re.compile(r'(password|secret)', re.IGNORECASE)
        for path, name, content, matches in reader.search_content_by_pattern(pattern):
            print(f"  {path}:")
            for line_num, line in matches:
                print(f"    Line {line_num}: {line.strip()}")
        print()

        # 5. Search with regex pattern for imports
        print("5. Search Python files with import statements:")
        for path, name, content, matches in reader.search_content_by_pattern(r'^import\s+\w+'):
            print(f"  {path}:")
            for line_num, line in matches:
                print(f"    Line {line_num}: {line.strip()}")
        print()

        # 6. Advanced combined search
        print("6. Advanced search: .py files containing 'def' functions:")
        for path, name, content, matches in reader.get_files_matching_patterns(
            name_pattern=r'\.py$',
            content_pattern=r'^def\s+\w+'):
            print(f"  {path}:")
            if matches:
                for line_num, line in matches:
                    print(f"    Line {line_num}: {line.strip()}")
        print()

        # 7. Search for configuration files with specific patterns
        print("7. Search config files containing port settings:")
        for path, name, content, matches in reader.get_files_matching_patterns(
            path_pattern=r'config/',
            content_pattern=r'port\s*=\s*\d+'):
            print(f"  {path}:")
            if matches:
                for line_num, line in matches:
                    print(f"    Line {line_num}: {line.strip()}")
        print()

        # 8. Search for files with specific naming patterns
        print("8. Search files with 'test' in filename:")
        for path, name, size in reader.search_files_by_name_pattern(r'test'):
            print(f"  {path} ({name}) - {size} bytes")
        print()

        # 9. Search for CSS files with color definitions
        print("9. Search CSS files with color definitions:")
        for path, name, content, matches in reader.get_files_matching_patterns(
            name_pattern=r'\.css$',
            content_pattern=r'color\s*:\s*[^;]+'):
            print(f"  {path}:")
            if matches:
                for line_num, line in matches:
                    print(f"    Line {line_num}: {line.strip()}")
        print()

        # 10. Complex regex search
        print("10. Search for email patterns in any file:")
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for path, name, content, matches in reader.search_content_by_pattern(email_pattern):
            print(f"  {path}:")
            for line_num, line in matches:
                print(f"    Line {line_num}: {line.strip()}")

    finally:
        # Clean up
        if os.path.exists(archive_path):
            os.remove(archive_path)
            print(f"\nCleaned up test archive: {archive_path}")


if __name__ == "__main__":
    demo_search_functionality()