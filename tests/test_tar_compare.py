#!/usr/bin/env python3
"""
Unit tests for tar_compare module.
"""

import unittest
import tempfile
import tarfile
import os
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tar_compare import TarFileComparer, TarComparisonResult


class TestTarFileComparer(unittest.TestCase):
    """Test cases for TarFileComparer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_test_archive(self, archive_name: str, files: dict) -> Path:
        """
        Create a test tar.gz archive with specified files.

        Args:
            archive_name: Name of the archive file
            files: Dictionary of {file_path: content}

        Returns:
            Path to created archive
        """
        archive_path = self.test_files_dir / archive_name

        with tempfile.TemporaryDirectory() as temp_content_dir:
            # Create files in temporary directory
            for file_path, content in files.items():
                full_path = Path(temp_content_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                if isinstance(content, str):
                    full_path.write_text(content, encoding='utf-8')
                else:
                    full_path.write_bytes(content)

            # Create tar.gz archive
            with tarfile.open(archive_path, 'w:gz') as tar:
                for file_path in files.keys():
                    full_path = Path(temp_content_dir) / file_path
                    tar.add(full_path, arcname=file_path)

        return archive_path

    def test_identical_files(self):
        """Test comparison of identical files."""
        content = "This is a test configuration file\nkey=value\nport=8080"

        source_archive = self._create_test_archive("source.tar.gz", {
            "config.rctl": content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "subfolder/config.rctl": content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertTrue(result.success)
        self.assertIn("identical", result.message.lower())
        self.assertEqual(result.source_file, "config.rctl")
        self.assertEqual(result.target_file, "subfolder/config.rctl")

    def test_different_files(self):
        """Test comparison of different files."""
        source_content = "source content"
        target_content = "target content"

        source_archive = self._create_test_archive("source.tar.gz", {
            "file.rctl": source_content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "file.rctl": target_content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("differ", result.message.lower())

    def test_extension_normalization(self):
        """Test that extensions are normalized correctly."""
        content = "test content"

        source_archive = self._create_test_archive("source.tar.gz", {
            "test.conf": content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "test.conf": content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))

        # Test with dot
        result1 = comparer.compare_files(".conf")
        self.assertTrue(result1.success)

        # Test without dot
        result2 = comparer.compare_files("conf")
        self.assertTrue(result2.success)

    def test_missing_file_in_source(self):
        """Test when file extension not found in source archive."""
        source_archive = self._create_test_archive("source.tar.gz", {
            "other.txt": "content"
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "file.rctl": "content"
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("no files", result.message.lower())
        self.assertIn("source archive", result.message.lower())

    def test_missing_file_in_target(self):
        """Test when file extension not found in target archive."""
        source_archive = self._create_test_archive("source.tar.gz", {
            "file.rctl": "content"
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "other.txt": "content"
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("no files", result.message.lower())
        self.assertIn("target archive", result.message.lower())

    def test_multiple_files_in_source(self):
        """Test when multiple files with same extension in source."""
        content = "test content"

        source_archive = self._create_test_archive("source.tar.gz", {
            "file1.rctl": content,
            "file2.rctl": content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "file.rctl": content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("multiple files", result.message.lower())
        self.assertIn("source archive", result.message.lower())

    def test_multiple_files_in_target(self):
        """Test when multiple files with same extension in target."""
        content = "test content"

        source_archive = self._create_test_archive("source.tar.gz", {
            "file.rctl": content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "file1.rctl": content,
            "file2.rctl": content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("multiple files", result.message.lower())
        self.assertIn("target archive", result.message.lower())

    def test_binary_files(self):
        """Test comparison of binary files."""
        binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd'

        source_archive = self._create_test_archive("source.tar.gz", {
            "data.bin": binary_content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "data.bin": binary_content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("bin")

        self.assertTrue(result.success)

    def test_different_binary_files(self):
        """Test comparison of different binary files."""
        source_content = b'\x00\x01\x02\x03'
        target_content = b'\x00\x01\x02\x04'

        source_archive = self._create_test_archive("source.tar.gz", {
            "data.bin": source_content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "data.bin": target_content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("bin")

        self.assertFalse(result.success)
        self.assertIn("differ", result.message.lower())

    def test_nonexistent_source_archive(self):
        """Test with nonexistent source archive."""
        target_archive = self._create_test_archive("target.tar.gz", {
            "file.rctl": "content"
        })

        comparer = TarFileComparer("nonexistent.tar.gz", str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())

    def test_nonexistent_target_archive(self):
        """Test with nonexistent target archive."""
        source_archive = self._create_test_archive("source.tar.gz", {
            "file.rctl": "content"
        })

        comparer = TarFileComparer(str(source_archive), "nonexistent.tar.gz")
        result = comparer.compare_files("rctl")

        self.assertFalse(result.success)
        self.assertIn("not found", result.message.lower())

    def test_case_insensitive_extension(self):
        """Test that extension matching is case insensitive."""
        content = "test content"

        source_archive = self._create_test_archive("source.tar.gz", {
            "file.RCTL": content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "file.rctl": content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("RCTL")

        self.assertTrue(result.success)

    def test_empty_files(self):
        """Test comparison of empty files."""
        source_archive = self._create_test_archive("source.tar.gz", {
            "empty.rctl": ""
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "empty.rctl": ""
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertTrue(result.success)

    def test_large_files(self):
        """Test comparison of larger files."""
        # Create a larger content
        large_content = "This is a line of content.\n" * 1000

        source_archive = self._create_test_archive("source.tar.gz", {
            "large.rctl": large_content
        })

        target_archive = self._create_test_archive("target.tar.gz", {
            "path/to/large.rctl": large_content
        })

        comparer = TarFileComparer(str(source_archive), str(target_archive))
        result = comparer.compare_files("rctl")

        self.assertTrue(result.success)


class TestTarComparisonResult(unittest.TestCase):
    """Test cases for TarComparisonResult class."""

    def test_success_result(self):
        """Test creation of success result."""
        result = TarComparisonResult(True, "Files are identical", "src.rctl", "tgt.rctl")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Files are identical")
        self.assertEqual(result.source_file, "src.rctl")
        self.assertEqual(result.target_file, "tgt.rctl")

    def test_failure_result(self):
        """Test creation of failure result."""
        result = TarComparisonResult(False, "Files differ")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Files differ")
        self.assertIsNone(result.source_file)
        self.assertIsNone(result.target_file)


if __name__ == '__main__':
    unittest.main()