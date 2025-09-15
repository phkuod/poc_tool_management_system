import tarfile
import os
import re
from contextlib import contextmanager
from typing import Iterator, Tuple, Optional, Union
from pathlib import Path


class TarFileReader:
    """
    A simple reader for .tar.gz files that can extract file information and content
    without extracting files to the filesystem.
    """

    def __init__(self, archive_path: Union[str, Path]):
        """
        Initialize with path to .tar.gz file.

        Args:
            archive_path: Path to the .tar.gz file
        """
        self.archive_path = str(archive_path)
        if not os.path.exists(self.archive_path):
            raise FileNotFoundError(f"Archive file not found: {self.archive_path}")

    def _compile_pattern(self, pattern: Union[str, re.Pattern[str]]) -> re.Pattern[str]:
        """Compile regex pattern if it's a string."""
        return re.compile(pattern) if isinstance(pattern, str) else pattern

    @contextmanager
    def _open_archive(self):
        """Context manager for opening archive."""
        with tarfile.open(self.archive_path, 'r:gz') as tar:
            yield tar

    def _get_file_members(self):
        """Generator for file members only (excludes directories)."""
        with self._open_archive() as tar:
            for member in tar.getmembers():
                if member.isfile():
                    yield member

    def list_files(self) -> Iterator[Tuple[str, str, int]]:
        """
        List all files in the archive.

        Yields:
            Tuple of (full_path, filename, size_in_bytes)
        """
        for member in self._get_file_members():
            filename = os.path.basename(member.name)
            yield (member.name, filename, member.size)

    def read_file(self, file_path: str) -> Optional[bytes]:
        """
        Read a specific file's content as bytes.

        Args:
            file_path: Full path of the file within the archive

        Returns:
            File content as bytes, or None if file not found
        """
        with self._open_archive() as tar:
            try:
                file_obj = tar.extractfile(file_path)
                if file_obj:
                    return file_obj.read()
                return None
            except KeyError:
                return None

    def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Read a specific file's content as text.

        Args:
            file_path: Full path of the file within the archive
            encoding: Text encoding (default: utf-8)

        Returns:
            File content as string, or None if file not found
        """
        content = self.read_file(file_path)
        if content:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                return None
        return None

    def get_all_files(self) -> Iterator[Tuple[str, str, bytes]]:
        """
        Get all files with their content.

        Yields:
            Tuple of (full_path, filename, content_as_bytes)
        """
        with self._open_archive() as tar:
            for member in tar.getmembers():
                if member.isfile():
                    filename = os.path.basename(member.name)
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        content = file_obj.read()
                        yield (member.name, filename, content)

    def get_all_text_files(self, encoding: str = 'utf-8') -> Iterator[Tuple[str, str, str]]:
        """
        Get all text files with their content.

        Args:
            encoding: Text encoding (default: utf-8)

        Yields:
            Tuple of (full_path, filename, content_as_string)
            Skips files that cannot be decoded as text
        """
        for full_path, filename, content in self.get_all_files():
            try:
                text_content = content.decode(encoding)
                yield (full_path, filename, text_content)
            except UnicodeDecodeError:
                # Skip files that cannot be decoded as text
                continue

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the archive.

        Args:
            file_path: Full path of the file within the archive

        Returns:
            True if file exists, False otherwise
        """
        with self._open_archive() as tar:
            try:
                member = tar.getmember(file_path)
                return member.isfile()
            except KeyError:
                return False

    def search_files_by_pattern(self, pattern: Union[str, re.Pattern[str]]) -> Iterator[Tuple[str, str, int]]:
        """
        Search files by regex pattern matching file paths.

        Args:
            pattern: Regex pattern string or compiled regex pattern

        Yields:
            Tuple of (full_path, filename, size_in_bytes) for matching files
        """
        compiled_pattern = self._compile_pattern(pattern)

        for member in self._get_file_members():
            if compiled_pattern.search(member.name):
                filename = os.path.basename(member.name)
                yield (member.name, filename, member.size)

    def search_files_by_name_pattern(self, pattern: Union[str, re.Pattern[str]]) -> Iterator[Tuple[str, str, int]]:
        """
        Search files by regex pattern matching only filenames (not full paths).

        Args:
            pattern: Regex pattern string or compiled regex pattern

        Yields:
            Tuple of (full_path, filename, size_in_bytes) for matching files
        """
        compiled_pattern = self._compile_pattern(pattern)

        for member in self._get_file_members():
            filename = os.path.basename(member.name)
            if compiled_pattern.search(filename):
                yield (member.name, filename, member.size)

    def search_files_by_extension(self, extension: str) -> Iterator[Tuple[str, str, int]]:
        """
        Search files by file extension.

        Args:
            extension: File extension (with or without leading dot)

        Yields:
            Tuple of (full_path, filename, size_in_bytes) for matching files
        """
        if not extension.startswith('.'):
            extension = '.' + extension

        pattern = re.compile(re.escape(extension) + '$', re.IGNORECASE)
        return self.search_files_by_pattern(pattern)

    def search_content_by_pattern(self, pattern: Union[str, re.Pattern[str]], encoding: str = 'utf-8') -> Iterator[Tuple[str, str, str, list]]:
        """
        Search file contents by regex pattern.

        Args:
            pattern: Regex pattern string or compiled regex pattern
            encoding: Text encoding (default: utf-8)

        Yields:
            Tuple of (full_path, filename, content, matching_lines)
            matching_lines is a list of (line_number, line_content) tuples
        """
        compiled_pattern = self._compile_pattern(pattern)

        for full_path, filename, content in self.get_all_text_files(encoding):
            matching_lines = []
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                if compiled_pattern.search(line):
                    matching_lines.append((line_num, line))

            if matching_lines:
                yield (full_path, filename, content, matching_lines)

    def get_files_matching_patterns(self, path_pattern: Optional[Union[str, re.Pattern[str]]] = None,
                                  name_pattern: Optional[Union[str, re.Pattern[str]]] = None,
                                  content_pattern: Optional[Union[str, re.Pattern[str]]] = None,
                                  encoding: str = 'utf-8') -> Iterator[Tuple[str, str, str, Optional[list]]]:
        """
        Advanced search combining path, name, and content patterns.

        Args:
            path_pattern: Regex pattern for full file paths
            name_pattern: Regex pattern for filenames only
            content_pattern: Regex pattern for file content
            encoding: Text encoding for content search

        Yields:
            Tuple of (full_path, filename, content, matching_lines)
            matching_lines is None if content_pattern is not provided
        """
        path_compiled = self._compile_pattern(path_pattern) if path_pattern else None
        name_compiled = self._compile_pattern(name_pattern) if name_pattern else None
        content_compiled = self._compile_pattern(content_pattern) if content_pattern else None

        for full_path, filename, content in self.get_all_text_files(encoding):
            # Check path pattern
            if path_compiled and not path_compiled.search(full_path):
                continue

            # Check name pattern
            if name_compiled and not name_compiled.search(filename):
                continue

            # Check content pattern
            matching_lines = None
            if content_compiled:
                matching_lines = []
                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if content_compiled.search(line):
                        matching_lines.append((line_num, line))

                # If content pattern provided but no matches, skip this file
                if not matching_lines:
                    continue

            yield (full_path, filename, content, matching_lines)

    def get_archive_info(self) -> dict:
        """
        Get basic information about the archive.

        Returns:
            Dictionary with archive statistics
        """
        file_count = 0
        total_size = 0

        with self._open_archive() as tar:
            for member in tar.getmembers():
                if member.isfile():
                    file_count += 1
                    total_size += member.size

        return {
            'archive_path': self.archive_path,
            'file_count': file_count,
            'total_uncompressed_size': total_size,
            'archive_size': os.path.getsize(self.archive_path)
        }


# Example usage
if __name__ == "__main__":
    # Example usage
    reader = TarFileReader("example.tar.gz")

    # List all files
    print("Files in archive:")
    for path, name, size in reader.list_files():
        print(f"  {path} ({name}) - {size} bytes")

    # Read a specific file
    content = reader.read_text_file("some/file.txt")
    if content:
        print(f"Content: {content}")

    # Get archive info
    info = reader.get_archive_info()
    print(f"Archive contains {info['file_count']} files")