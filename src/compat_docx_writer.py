"""
Compatibility wrapper for SafeDocxEngine that maintains the original DocxWriter interface.
This allows drop-in replacement without breaking existing code.
"""

from pathlib import Path
from typing import Dict, List
from src.safe_docx_engine import SafeDocxEngine


class DocxWriter:
    """
    Compatibility wrapper that provides the same interface as the original DocxWriter
    but uses the new SafeDocxEngine internally.
    """
    
    def __init__(self, template_path: Path):
        """
        Initialize with template path.
        
        Args:
            template_path: Path to Master_Resume.docx
        """
        self._engine = SafeDocxEngine(template_path)
    
    def get_section_names(self) -> List[str]:
        """Get list of all detected placeholder names."""
        return self._engine.get_placeholder_names()
    
    def get_original_content(self, placeholder_name: str) -> str:
        """
        Get original template content for a given placeholder.
        
        For compatibility, returns the placeholder pattern itself.
        """
        return f"{{{{{placeholder_name}}}}}"
    
    def replace_placeholders(self, replacements: Dict[str, str]) -> int:
        """
        Replace placeholders with provided content.
        
        Args:
            replacements: Dict mapping placeholder_name → replacement_text
            
        Returns:
            Number of placeholders replaced
        """
        stats = self._engine.replace_placeholders(replacements)
        return stats["replaced"]
    
    def save(self, output_path: Path) -> None:
        """Save the modified document."""
        self._engine.save(output_path)
    
    # Additional methods for backward compatibility
    def debug_structure(self) -> None:
        """Debug method - prints placeholder information."""
        names = self.get_section_names()
        print(f"Found {len(names)} placeholders: {names}")
    
    @property
    def document(self):
        """Provide access to the underlying document for advanced usage."""
        return self._engine.document


def scan_template(template_path: Path) -> Dict[str, int]:
    """
    Compatibility function: scan a template and return placeholder counts.
    
    Args:
        template_path: Path to template file
        
    Returns:
        Dict mapping placeholder_name → occurrence_count
    """
    engine = SafeDocxEngine(template_path)
    counts = {name: engine.get_placeholder_count(name) for name in engine.get_placeholder_names()}
    return counts


if __name__ == "__main__":
    # Test compatibility
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.compat_docx_writer <template.docx>")
        sys.exit(1)
    
    counts = scan_template(Path(sys.argv[1]))
    print("\nPlaceholder Summary:")
    for name, count in sorted(counts.items()):
        print(f"  {name}: {count} occurrence(s)")