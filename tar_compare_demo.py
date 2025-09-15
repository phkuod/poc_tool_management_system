#!/usr/bin/env python3
"""
Demo script showing tar_compare functionality with example usage.
"""

import tempfile
import tarfile
import os
from pathlib import Path
from tar_compare import TarFileComparer


def create_demo_archives():
    """Create demo tar.gz files for testing."""
    # Demo content
    rctl_content = """# Control configuration file
version=1.0
timeout=30
max_retries=3
debug=false
log_level=INFO
"""

    different_rctl_content = """# Control configuration file
version=1.1
timeout=60
max_retries=5
debug=true
log_level=DEBUG
"""

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <database>
        <host>localhost</host>
        <port>5432</port>
        <name>production</name>
    </database>
    <logging>
        <level>INFO</level>
        <format>json</format>
    </logging>
</configuration>"""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create source archive with .rctl file at root
        source_dir = temp_path / "source"
        source_dir.mkdir()
        (source_dir / "config.rctl").write_text(rctl_content)
        (source_dir / "settings.xml").write_text(xml_content)
        (source_dir / "readme.txt").write_text("This is a readme file")

        source_archive = "demo_source.tar.gz"
        with tarfile.open(source_archive, 'w:gz') as tar:
            tar.add(source_dir / "config.rctl", arcname="config.rctl")
            tar.add(source_dir / "settings.xml", arcname="settings.xml")
            tar.add(source_dir / "readme.txt", arcname="readme.txt")

        # Create target archive with .rctl file in subfolder (identical content)
        target_dir = temp_path / "target"
        target_dir.mkdir()
        target_subdir = target_dir / "configs"
        target_subdir.mkdir()
        (target_subdir / "app.rctl").write_text(rctl_content)  # Same content
        (target_dir / "settings.xml").write_text(xml_content)  # Same content
        (target_dir / "other.txt").write_text("Other file")

        target_archive = "demo_target.tar.gz"
        with tarfile.open(target_archive, 'w:gz') as tar:
            tar.add(target_subdir / "app.rctl", arcname="configs/app.rctl")
            tar.add(target_dir / "settings.xml", arcname="settings.xml")
            tar.add(target_dir / "other.txt", arcname="other.txt")

        # Create different archive with different .rctl content
        different_dir = temp_path / "different"
        different_dir.mkdir()
        (different_dir / "config.rctl").write_text(different_rctl_content)  # Different content
        (different_dir / "settings.xml").write_text(xml_content)

        different_archive = "demo_different.tar.gz"
        with tarfile.open(different_archive, 'w:gz') as tar:
            tar.add(different_dir / "config.rctl", arcname="config.rctl")
            tar.add(different_dir / "settings.xml", arcname="settings.xml")

        return source_archive, target_archive, different_archive


def demo_successful_comparison():
    """Demonstrate successful file comparison."""
    print("=== SUCCESSFUL COMPARISON ===")
    print("Comparing .rctl files between source and target archives...")
    print()

    source_archive, target_archive, _ = create_demo_archives()

    try:
        comparer = TarFileComparer(source_archive, target_archive)
        result = comparer.compare_files("rctl")

        print(f"Comparison result: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Message: {result.message}")
        if result.source_file and result.target_file:
            print(f"Source file: {result.source_file}")
            print(f"Target file: {result.target_file}")
        print()

    finally:
        for archive in [source_archive, target_archive]:
            if os.path.exists(archive):
                os.remove(archive)


def demo_failed_comparison():
    """Demonstrate failed file comparison."""
    print("=== FAILED COMPARISON ===")
    print("Comparing .rctl files with different content...")
    print()

    source_archive, _, different_archive = create_demo_archives()

    try:
        comparer = TarFileComparer(source_archive, different_archive)
        result = comparer.compare_files("rctl")

        print(f"Comparison result: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Message: {result.message}")
        if result.source_file and result.target_file:
            print(f"Source file: {result.source_file}")
            print(f"Target file: {result.target_file}")
        print()

    finally:
        for archive in [source_archive, different_archive]:
            if os.path.exists(archive):
                os.remove(archive)


def demo_different_extensions():
    """Demonstrate comparison with different file extensions."""
    print("=== DIFFERENT EXTENSIONS ===")
    print("Comparing .xml files between archives...")
    print()

    source_archive, target_archive, _ = create_demo_archives()

    try:
        comparer = TarFileComparer(source_archive, target_archive)

        # Compare XML files
        result = comparer.compare_files("xml")
        print(f"XML comparison: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Message: {result.message}")
        print()

        # Try comparing non-existent extension
        result = comparer.compare_files("json")
        print(f"JSON comparison: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Message: {result.message}")
        print()

    finally:
        for archive in [source_archive, target_archive]:
            if os.path.exists(archive):
                os.remove(archive)


def demo_cli_examples():
    """Show CLI usage examples."""
    print("=== CLI USAGE EXAMPLES ===")
    print()
    print("Basic usage:")
    print("  python tar_compare.py source.tar.gz target.tar.gz --ext rctl")
    print()
    print("With verbose output:")
    print("  python tar_compare.py source.tar.gz target.tar.gz --ext rctl --verbose")
    print()
    print("Different extensions:")
    print("  python tar_compare.py source.tar.gz target.tar.gz --ext .conf")
    print("  python tar_compare.py source.tar.gz target.tar.gz --ext xml")
    print("  python tar_compare.py source.tar.gz target.tar.gz --ext .properties")
    print()
    print("Exit codes:")
    print("  0 = Files are identical")
    print("  1 = Files differ or error occurred")
    print()


def main():
    """Run tar comparison demonstration."""
    print("Tar.gz File Comparison Tool - Demo")
    print("=" * 50)
    print()

    demo_successful_comparison()
    demo_failed_comparison()
    demo_different_extensions()
    demo_cli_examples()

    print("Demo complete!")


if __name__ == "__main__":
    main()