#!/usr/bin/env python3
"""
Comprehensive demo script showing TarFileReader functionality including
the new regex search capabilities and optimized performance.
"""

import os
import tempfile
import tarfile
import re
from tar_file_reader import TarFileReader


def create_enhanced_demo_archive():
    """Create a comprehensive demo .tar.gz file with various file types."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Enhanced demo files with more variety
        demo_files = {
            # Configuration files
            'config/app.conf': 'server_port=8080\ndebug=true\nlog_level=INFO\napi_key=secret123\nmax_connections=1000',
            'config/database.ini': '[database]\nhost=localhost\nport=5432\nuser=admin\npassword=admin123\ntimeout=30',

            # Source code files
            'src/main.py': '''#!/usr/bin/env python3
import sys
import logging

def main():
    """Main application entry point."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Application starting...")
    print("Hello World from TarFileReader demo!")
    return 0

if __name__ == "__main__":
    sys.exit(main())''',

            'src/utils.py': '''import re
import json
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
    return bool(re.match(pattern, email))

def load_config(file_path: str) -> Optional[dict]:
    """Load JSON configuration file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

class DatabaseConnection:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connected = False

    def connect(self):
        """Connect to database."""
        print(f"Connecting to {self.host}:{self.port}")
        self.connected = True

    def disconnect(self):
        """Disconnect from database."""
        self.connected = False''',

            # Data files
            'data/users.csv': '''id,name,email,department,salary
1,Alice Johnson,alice@company.com,Engineering,75000
2,Bob Smith,bob@company.com,Marketing,65000
3,Carol Davis,carol@company.com,Engineering,80000
4,David Wilson,david@company.com,Sales,70000
5,Eve Brown,eve@company.com,Engineering,85000''',

            'data/logs.txt': '''2024-01-01 10:00:00 INFO Server started on port 8080
2024-01-01 10:01:00 DEBUG Connected to database
2024-01-01 10:02:00 ERROR Connection failed to external service
2024-01-01 10:03:00 WARN Retrying connection in 5 seconds
2024-01-01 10:04:00 INFO Connection restored
2024-01-01 10:05:00 DEBUG Processing user request
2024-01-01 10:06:00 ERROR Invalid user credentials
2024-01-01 10:07:00 INFO User authentication successful''',

            'data/metrics.json': '''{"server_stats": {"uptime": 86400, "requests": 15432, "errors": 23},
"user_stats": {"active_users": 1250, "new_registrations": 45},
"performance": {"avg_response_time": 120, "memory_usage": 0.75}}''',

            # Documentation
            'docs/README.md': '''# TarFileReader Demo Project

This is a comprehensive demonstration of TarFileReader capabilities.

## Features

- **File Reading**: Read any file content without extraction
- **Pattern Search**: Regex-based file and content searching
- **Performance**: Optimized for large archives
- **Type Safety**: Full type hints and error handling

## Usage Examples

```python
reader = TarFileReader("archive.tar.gz")

# List all files
for path, name, size in reader.list_files():
    print(f"{path} - {size} bytes")

# Search for Python files
for path, name, size in reader.search_files_by_extension("py"):
    print(f"Python file: {path}")

# Search content
for path, name, content, matches in reader.search_content_by_pattern("def\\s+\\w+"):
    print(f"Functions in {path}")
```

## Performance Notes

The reader uses memory-efficient iterators and context managers for optimal performance.
''',

            'docs/API.md': '''# API Documentation

## TarFileReader Class

### Basic Operations
- `list_files()` - List all files
- `read_file(path)` - Read binary content
- `read_text_file(path)` - Read text content
- `file_exists(path)` - Check file existence

### Search Operations
- `search_files_by_pattern(regex)` - Search file paths
- `search_files_by_name_pattern(regex)` - Search filenames
- `search_files_by_extension(ext)` - Search by extension
- `search_content_by_pattern(regex)` - Search file contents
- `get_files_matching_patterns()` - Advanced combined search

### Utility Operations
- `get_archive_info()` - Archive statistics
- `get_all_files()` - All files with content
- `get_all_text_files()` - All text files with content
''',

            # Test files
            'tests/test_main.py': '''import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main_returns_zero(self):
        """Test that main returns 0 on success."""
        result = main()
        self.assertEqual(result, 0)

    def test_main_function_exists(self):
        """Test that main function is callable."""
        self.assertTrue(callable(main))

if __name__ == "__main__":
    unittest.main()''',

            'tests/test_utils.py': '''import unittest
from src.utils import validate_email, DatabaseConnection

class TestUtils(unittest.TestCase):
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "admin@company.org"
        ]
        for email in valid_emails:
            self.assertTrue(validate_email(email), f"Should validate {email}")

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com"
        ]
        for email in invalid_emails:
            self.assertFalse(validate_email(email), f"Should reject {email}")

    def test_database_connection(self):
        """Test database connection class."""
        conn = DatabaseConnection("localhost", 5432, "user", "pass")
        self.assertFalse(conn.connected)

        conn.connect()
        self.assertTrue(conn.connected)

        conn.disconnect()
        self.assertFalse(conn.connected)''',

            # Web files
            'web/index.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TarFileReader Demo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="header">
        <h1>TarFileReader Demonstration</h1>
    </header>
    <main class="content">
        <p>This archive contains various file types to demonstrate search capabilities.</p>
        <div class="features">
            <h2>Features</h2>
            <ul>
                <li>Pattern-based file search</li>
                <li>Content search with regex</li>
                <li>Performance optimizations</li>
            </ul>
        </div>
    </main>
    <script src="app.js"></script>
</body>
</html>''',

            'web/style.css': '''/* TarFileReader Demo Styles */
body {
    margin: 0;
    padding: 20px;
    font-family: 'Arial', sans-serif;
    background-color: #f5f5f5;
    color: #333;
}

.header {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.header h1 {
    margin: 0;
    font-size: 2.5em;
}

.content {
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.features ul {
    list-style-type: none;
    padding: 0;
}

.features li {
    padding: 10px;
    margin: 5px 0;
    background-color: #ecf0f1;
    border-left: 4px solid #3498db;
}

.error {
    color: #e74c3c;
    font-weight: bold;
}

.success {
    color: #27ae60;
    font-weight: bold;
}''',

            'web/app.js': '''// TarFileReader Demo JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('TarFileReader demo page loaded');

    // Simulate some dynamic content
    const features = document.querySelector('.features ul');
    if (features) {
        const newFeature = document.createElement('li');
        newFeature.textContent = 'Dynamic content loading';
        features.appendChild(newFeature);
    }

    // Add click handler for demonstration
    document.addEventListener('click', function(event) {
        if (event.target.tagName === 'LI') {
            event.target.style.backgroundColor = '#d5dbdb';
        }
    });
});

function validateInput(input) {
    const emailPattern = /^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$/;
    return emailPattern.test(input);
}''',
        }

        # Write demo files
        for file_path, content in demo_files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Create tar.gz archive
        archive_path = 'comprehensive_demo.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            for file_path in demo_files.keys():
                full_path = os.path.join(temp_dir, file_path)
                tar.add(full_path, arcname=file_path)

        return archive_path


def demo_basic_functionality():
    """Demonstrate basic TarFileReader functionality."""
    print("=== BASIC FUNCTIONALITY ===")

    archive_path = create_enhanced_demo_archive()
    reader = TarFileReader(archive_path)

    try:
        # Archive information
        print("Archive Information:")
        info = reader.get_archive_info()
        print(f"  Files: {info['file_count']}")
        print(f"  Total size: {info['total_uncompressed_size']:,} bytes")
        print(f"  Archive size: {info['archive_size']:,} bytes")
        print()

        # List first 5 files
        print("First 5 files:")
        for i, (path, name, size) in enumerate(reader.list_files()):
            if i >= 5:
                break
            print(f"  {path} ({size:,} bytes)")
        print()

        # Read specific file
        print("Reading config/app.conf:")
        config_content = reader.read_text_file('config/app.conf')
        if config_content:
            for line in config_content.strip().split('\n')[:3]:  # First 3 lines
                print(f"  {line}")
            print("  ...")
        print()

    finally:
        os.remove(archive_path)


def demo_search_functionality():
    """Demonstrate advanced search functionality."""
    print("=== SEARCH FUNCTIONALITY ===")

    archive_path = create_enhanced_demo_archive()
    reader = TarFileReader(archive_path)

    try:
        # 1. Search by file extension
        print("1. Python files (.py extension):")
        for path, name, size in reader.search_files_by_extension('py'):
            print(f"  {path} ({size:,} bytes)")
        print()

        # 2. Search by path pattern
        print("2. Files in 'src/' directory:")
        for path, name, size in reader.search_files_by_pattern(r'^src/'):
            print(f"  {path} ({size:,} bytes)")
        print()

        # 3. Search by filename pattern
        print("3. Test files (filename contains 'test'):")
        for path, name, size in reader.search_files_by_name_pattern(r'test'):
            print(f"  {path} ({size:,} bytes)")
        print()

        # 4. Search content for function definitions
        print("4. Python function definitions:")
        func_pattern = r'^def\s+\w+\s*\('
        for path, name, content, matches in reader.search_content_by_pattern(func_pattern):
            print(f"  {path}:")
            for line_num, line in matches[:2]:  # Show first 2 matches
                print(f"    Line {line_num}: {line.strip()}")
            if len(matches) > 2:
                print(f"    ... and {len(matches) - 2} more matches")
        print()

        # 5. Search for email addresses
        print("5. Email addresses in files:")
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for path, name, content, matches in reader.search_content_by_pattern(email_pattern):
            print(f"  {path}: {len(matches)} email(s) found")
            for line_num, line in matches[:3]:  # Show first 3
                # Extract just the email from the line
                emails = re.findall(email_pattern, line)
                for email in emails:
                    print(f"    Line {line_num}: {email}")
        print()

        # 6. Advanced combined search
        print("6. Advanced search - Python files with 'import' statements:")
        for path, name, content, matches in reader.get_files_matching_patterns(
            name_pattern=r'\.py$',
            content_pattern=r'^import\s+\w+'):
            print(f"  {path}:")
            for line_num, line in matches[:3]:  # Show first 3 imports
                print(f"    Line {line_num}: {line.strip()}")
            if len(matches) > 3:
                print(f"    ... and {len(matches) - 3} more imports")
        print()

        # 7. Search configuration files
        print("7. Configuration values (port/password settings):")
        config_pattern = r'(port|password)\s*[=:]\s*\w+'
        for path, name, content, matches in reader.get_files_matching_patterns(
            path_pattern=r'^config/',
            content_pattern=config_pattern):
            print(f"  {path}:")
            for line_num, line in matches:
                print(f"    Line {line_num}: {line.strip()}")
        print()

    finally:
        os.remove(archive_path)


def demo_performance_features():
    """Demonstrate performance and optimization features."""
    print("=== PERFORMANCE FEATURES ===")

    archive_path = create_enhanced_demo_archive()
    reader = TarFileReader(archive_path)

    try:
        # Demonstrate efficient iteration
        print("File type distribution:")
        extensions = {}
        for path, name, size in reader.list_files():
            ext = os.path.splitext(name)[1].lower() or 'no-extension'
            extensions[ext] = extensions.get(ext, 0) + 1

        for ext, count in sorted(extensions.items()):
            print(f"  {ext}: {count} files")
        print()

        # Demonstrate compiled pattern reuse
        print("Demonstrating pattern compilation optimization:")
        pattern = re.compile(r'class\s+\w+', re.MULTILINE)

        class_count = 0
        for path, name, content, matches in reader.search_content_by_pattern(pattern):
            class_count += len(matches)
            if matches:
                print(f"  {path}: {len(matches)} class definition(s)")

        print(f"Total classes found: {class_count}")
        print()

        # Show memory-efficient processing
        print("Large file handling (showing file size distribution):")
        sizes = [size for _, _, size in reader.list_files()]
        if sizes:
            print(f"  Smallest file: {min(sizes):,} bytes")
            print(f"  Largest file: {max(sizes):,} bytes")
            print(f"  Average size: {sum(sizes) // len(sizes):,} bytes")
        print()

    finally:
        os.remove(archive_path)


def demo_error_handling():
    """Demonstrate error handling and edge cases."""
    print("=== ERROR HANDLING ===")

    archive_path = create_enhanced_demo_archive()
    reader = TarFileReader(archive_path)

    try:
        # Test file existence
        print("File existence checks:")
        test_files = ['src/main.py', 'nonexistent.txt', 'config/app.conf', 'missing/file.xyz']
        for file_path in test_files:
            exists = reader.file_exists(file_path)
            status = "EXISTS" if exists else "NOT FOUND"
            print(f"  {file_path}: {status}")
        print()

        # Test reading non-existent file
        print("Reading non-existent file:")
        content = reader.read_text_file('does/not/exist.txt')
        print(f"  Result: {content}")
        print()

        # Test invalid patterns
        print("Pattern handling:")
        try:
            # Valid pattern
            results = list(reader.search_files_by_pattern(r'\.py$'))
            print(f"  Valid pattern '\.py$': {len(results)} matches")

            # Pre-compiled pattern
            compiled = re.compile(r'config/')
            results = list(reader.search_files_by_pattern(compiled))
            print(f"  Compiled pattern: {len(results)} matches")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    finally:
        os.remove(archive_path)


def main():
    """Run comprehensive TarFileReader demonstration."""
    print("TarFileReader Comprehensive Demonstration")
    print("=" * 60)
    print()

    demo_basic_functionality()
    print()

    demo_search_functionality()
    print()

    demo_performance_features()
    print()

    demo_error_handling()
    print()

    print("Demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()