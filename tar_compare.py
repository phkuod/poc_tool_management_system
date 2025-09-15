#!/usr/bin/env python3
"""
Tar.gz file comparison tool that compares files with specified extension between two archives.
Validates that files with the same extension are identical between source and target tar.gz files.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from tar_file_reader import TarFileReader


class TarComparisonResult:
    """Result object for tar comparison operations."""

    def __init__(self, success: bool, message: str, source_file: Optional[str] = None,
                 target_file: Optional[str] = None):
        self.success = success
        self.message = message
        self.source_file = source_file
        self.target_file = target_file


class TarFileComparer:
    """Compares files with specified extension between two tar.gz archives."""

    def __init__(self, source_path: str, target_path: str):
        """
        Initialize comparer with paths to source and target tar.gz files.

        Args:
            source_path: Path to source tar.gz file
            target_path: Path to target tar.gz file
        """
        self.source_path = source_path
        self.target_path = target_path

    def _normalize_extension(self, extension: str) -> str:
        """Normalize extension format to include leading dot."""
        if not extension.startswith('.'):
            extension = '.' + extension
        return extension.lower()

    def _find_files_by_extension(self, reader: TarFileReader, extension: str) -> List[Tuple[str, str, int]]:
        """Find all files with specified extension in archive."""
        return list(reader.search_files_by_extension(extension))

    def compare_files(self, extension: str) -> TarComparisonResult:
        """
        Compare files with specified extension between source and target archives.

        Args:
            extension: File extension to compare (with or without leading dot)

        Returns:
            TarComparisonResult with comparison outcome
        """
        extension = self._normalize_extension(extension)

        try:
            # Initialize readers
            source_reader = TarFileReader(self.source_path)
            target_reader = TarFileReader(self.target_path)

            # Find files with specified extension
            source_files = self._find_files_by_extension(source_reader, extension)
            target_files = self._find_files_by_extension(target_reader, extension)

            # Validate file existence
            if not source_files:
                return TarComparisonResult(
                    False,
                    f"No files with extension '{extension}' found in source archive: {self.source_path}"
                )

            if not target_files:
                return TarComparisonResult(
                    False,
                    f"No files with extension '{extension}' found in target archive: {self.target_path}"
                )

            # Handle multiple files with same extension
            if len(source_files) > 1:
                return TarComparisonResult(
                    False,
                    f"Multiple files with extension '{extension}' found in source archive. "
                    f"Found: {[f[0] for f in source_files]}"
                )

            if len(target_files) > 1:
                return TarComparisonResult(
                    False,
                    f"Multiple files with extension '{extension}' found in target archive. "
                    f"Found: {[f[0] for f in target_files]}"
                )

            # Get file paths
            source_file_path = source_files[0][0]
            target_file_path = target_files[0][0]

            # Read file contents
            source_content = source_reader.read_file(source_file_path)
            target_content = target_reader.read_file(target_file_path)

            if source_content is None:
                return TarComparisonResult(
                    False,
                    f"Failed to read source file: {source_file_path}"
                )

            if target_content is None:
                return TarComparisonResult(
                    False,
                    f"Failed to read target file: {target_file_path}"
                )

            # Compare file contents
            if source_content == target_content:
                return TarComparisonResult(
                    True,
                    f"Files are identical: source '{source_file_path}' matches target '{target_file_path}'",
                    source_file_path,
                    target_file_path
                )
            else:
                return TarComparisonResult(
                    False,
                    f"Files differ: source '{source_file_path}' ({len(source_content)} bytes) "
                    f"vs target '{target_file_path}' ({len(target_content)} bytes)",
                    source_file_path,
                    target_file_path
                )

        except FileNotFoundError as e:
            return TarComparisonResult(False, f"Archive file not found: {e}")
        except Exception as e:
            return TarComparisonResult(False, f"Error during comparison: {e}")


def main():
    """Command-line interface for tar file comparison."""
    parser = argparse.ArgumentParser(
        description="Compare files with specified extension between two tar.gz archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s source.tar.gz target.tar.gz --ext rctl
  %(prog)s source.tar.gz target.tar.gz --ext .conf
  %(prog)s source.tar.gz target.tar.gz --extension xml
        """
    )

    parser.add_argument('source', help='Path to source tar.gz file')
    parser.add_argument('target', help='Path to target tar.gz file')
    parser.add_argument('--ext', '--extension', dest='extension', required=True,
                       help='File extension to compare (with or without leading dot)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    # Validate input files exist
    source_path = Path(args.source)
    target_path = Path(args.target)

    if not source_path.exists():
        print(f"Error: Source file does not exist: {source_path}", file=sys.stderr)
        sys.exit(1)

    if not target_path.exists():
        print(f"Error: Target file does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    # Perform comparison
    comparer = TarFileComparer(str(source_path), str(target_path))
    result = comparer.compare_files(args.extension)

    # Output results
    if args.verbose:
        print(f"Source archive: {source_path}")
        print(f"Target archive: {target_path}")
        print(f"Extension: {args.extension}")
        print(f"Result: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Message: {result.message}")
        if result.source_file and result.target_file:
            print(f"Source file: {result.source_file}")
            print(f"Target file: {result.target_file}")
    else:
        print(result.message)

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()