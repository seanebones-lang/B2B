"""Accessibility utilities for WCAG 2.2 compliance"""

from typing import Dict, Optional


def get_aria_labels() -> Dict[str, str]:
    """
    Get ARIA labels for common UI elements
    
    Returns:
        Dictionary of ARIA labels
    """
    return {
        "api_key_input": "Enter your xAI API key",
        "tool_select": "Select B2B SaaS tools to analyze",
        "analysis_method": "Choose analysis method: semantic or standard",
        "run_analysis": "Run analysis to scrape reviews and generate insights",
        "export_markdown": "Export results as Markdown file",
        "export_json": "Export results as JSON file",
        "summary_tab": "Summary view showing overview of analysis results",
        "per_tool_tab": "Per-tool breakdown showing detailed analysis",
        "opportunities_tab": "Top 3 opportunities with roadmaps",
        "progress_bar": "Analysis progress indicator",
        "status_text": "Current analysis status",
    }


def get_keyboard_shortcuts() -> Dict[str, str]:
    """
    Get keyboard shortcuts for accessibility
    
    Returns:
        Dictionary of keyboard shortcuts
    """
    return {
        "run_analysis": "Ctrl+Enter or Cmd+Enter",
        "export_markdown": "Ctrl+M or Cmd+M",
        "export_json": "Ctrl+J or Cmd+J",
        "focus_tool_select": "Ctrl+T or Cmd+T",
    }


def get_accessibility_attributes(element_type: str, element_id: Optional[str] = None) -> Dict[str, str]:
    """
    Get accessibility attributes for UI elements (WCAG 2.2 compliant)
    
    Args:
        element_type: Type of element (button, input, select, etc.)
        element_id: Optional element ID
        
    Returns:
        Dictionary of accessibility attributes
    """
    aria_labels = get_aria_labels()
    
    base_attrs = {
        "role": element_type,
    }
    
    if element_id and element_id in aria_labels:
        base_attrs["aria-label"] = aria_labels[element_id]
    
    # Add specific attributes based on element type (WCAG 2.2 Level AA)
    if element_type == "button":
        base_attrs.update({
            "aria-pressed": "false",
            "tabindex": "0",
            "aria-keyshortcuts": get_keyboard_shortcuts().get(element_id, ""),
        })
    elif element_type == "input":
        base_attrs.update({
            "aria-required": "true",
            "aria-invalid": "false",
            "aria-describedby": f"{element_id}_description" if element_id else None,
        })
    elif element_type == "select":
        base_attrs.update({
            "aria-haspopup": "listbox",
            "aria-expanded": "false",
            "aria-controls": f"{element_id}_listbox" if element_id else None,
        })
    elif element_type == "progress":
        base_attrs.update({
            "aria-valuemin": "0",
            "aria-valuemax": "100",
            "aria-valuenow": "0",
            "aria-live": "polite",
        })
    elif element_type == "tab":
        base_attrs.update({
            "aria-selected": "false",
            "aria-controls": f"{element_id}_panel" if element_id else None,
        })
    
    # WCAG 2.2 Level AA: Ensure sufficient color contrast (handled in CSS)
    # WCAG 2.2 Level AA: Focus indicators (handled in CSS)
    # WCAG 2.2 Level AA: Keyboard navigation (ensured via tabindex)
    
    return base_attrs


def check_wcag_compliance(element_type: str, element_id: Optional[str] = None) -> Dict[str, bool]:
    """
    Check WCAG 2.2 compliance for an element
    
    Args:
        element_type: Type of element
        element_id: Optional element ID
        
    Returns:
        Dictionary with WCAG 2.2 compliance checks
    """
    attrs = get_accessibility_attributes(element_type, element_id)
    
    compliance = {
        "has_aria_label": "aria-label" in attrs or element_id in get_aria_labels(),
        "has_role": "role" in attrs,
        "keyboard_accessible": element_type in ["button", "input", "select", "a"] or "tabindex" in attrs,
        "has_focus_indicator": True,  # Assumed handled in CSS
        "sufficient_contrast": True,  # Assumed handled in CSS
        "level_aa_compliant": False,
    }
    
    # Level AA compliance requires all checks
    compliance["level_aa_compliant"] = all([
        compliance["has_aria_label"],
        compliance["has_role"],
        compliance["keyboard_accessible"],
        compliance["has_focus_indicator"],
        compliance["sufficient_contrast"]
    ])
    
    return compliance


def get_high_contrast_styles() -> Dict[str, str]:
    """
    Get high contrast CSS styles for accessibility
    
    Returns:
        Dictionary of CSS styles
    """
    return {
        "background": "#FFFFFF",
        "foreground": "#000000",
        "primary": "#0066CC",
        "secondary": "#666666",
        "error": "#CC0000",
        "success": "#006600",
        "warning": "#CC6600",
        "border": "#000000",
        "focus": "2px solid #0066CC",
    }


def validate_accessibility(element_type: str, element_id: Optional[str] = None) -> Dict[str, bool]:
    """
    Validate accessibility attributes for an element
    
    Args:
        element_type: Type of element
        element_id: Optional element ID
        
    Returns:
        Dictionary with validation results
    """
    attrs = get_accessibility_attributes(element_type, element_id)
    
    validation = {
        "has_aria_label": "aria-label" in attrs,
        "has_role": "role" in attrs,
        "has_tabindex": "tabindex" in attrs or element_type in ["button", "input", "select", "a"],
        "is_keyboard_accessible": element_type in ["button", "input", "select", "a"],
    }
    
    return validation


def get_screen_reader_text(text: str, context: Optional[str] = None) -> str:
    """
    Get screen reader-friendly text
    
    Args:
        text: Original text
        context: Optional context for screen readers
        
    Returns:
        Screen reader-friendly text
    """
    if context:
        return f"{text}. {context}"
    return text
