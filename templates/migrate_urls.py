#!/usr/bin/env python3
"""
Template URL Migration Script

This script updates all url_for() calls in your templates to use the new
blueprint-based route names.

WHAT IT DOES:
- Scans all .html files in the templates/ folder
- Finds url_for('old_name', ...) patterns
- Replaces them with url_for('blueprint.new_name', ...)
- Creates backups of original files (filename.html.backup)

USAGE:
    # From your project root:
    uv run python migrate_urls.py
    
    # To see what would change without making changes:
    uv run python migrate_urls.py --dry-run

AFTER RUNNING:
    1. Review the changes shown in the output
    2. Test your app to make sure everything works
    3. Delete the .backup files once you're satisfied
"""
import os
import re
import sys
from pathlib import Path


# Mapping of old route names to new blueprint.route names
URL_MAPPINGS = {
    # Main routes
    'index': 'main.index',
    
    # Auth routes
    'login': 'auth.login',
    'logout': 'auth.logout',
    'register': 'auth.register',
    'forgot_password': 'auth.forgot_password',
    'forgotpassword': 'auth.forgot_password',  # In case you used this variant
    'reset_password': 'auth.reset_password',
    'resetpassword': 'auth.reset_password',  # In case you used this variant
    
    # Box routes
    'dashboard': 'boxes.dashboard',
    'create_box': 'boxes.create_box',
    'view_box': 'boxes.view_box',
    'edit_box': 'boxes.edit_box',
    'delete_box': 'boxes.delete_box',
    'regenerate_qr': 'boxes.regenerate_qr',
    
    # Item routes
    'create_item': 'items.create_item',
    'edit_item': 'items.edit_item',
    'delete_item': 'items.delete_item',
    'move_item': 'items.move_item',
    'duplicate_item': 'items.duplicate_item',
    
    # Scanner routes
    'scanner': 'scanner.scanner',
    'scan': 'scanner.scanner',  # In case you used 'scan' instead of 'scanner'
    'scan_redirect': 'scanner.scan_redirect',
    'qr_redirect': 'scanner.scan_redirect',  # In case you used this variant
    'search': 'scanner.search',
}


def find_template_files(templates_dir: Path) -> list[Path]:
    """Find all HTML template files."""
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        sys.exit(1)
    
    files = list(templates_dir.rglob("*.html"))
    # Exclude backup files
    files = [f for f in files if not f.name.endswith('.backup')]
    return files


def update_url_for_calls(content: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Update url_for() calls in the content.
    
    Returns:
        Tuple of (updated_content, list of (old, new) replacements made)
    """
    changes = []
    
    # Pattern to match url_for('route_name' or url_for("route_name"
    # Captures: the quote type, the route name
    pattern = r"url_for\(['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]"
    
    def replace_match(match):
        full_match = match.group(0)
        route_name = match.group(1)
        
        # Check if this route needs updating
        if route_name in URL_MAPPINGS:
            new_route = URL_MAPPINGS[route_name]
            # Preserve the quote style used
            quote = "'" if "'" in full_match else '"'
            new_match = f"url_for({quote}{new_route}{quote}"
            changes.append((route_name, new_route))
            return new_match
        
        # Already has a dot (already using blueprint syntax) - skip
        if '.' in route_name:
            return full_match
        
        # Unknown route - leave unchanged but warn
        return full_match
    
    updated_content = re.sub(pattern, replace_match, content)
    return updated_content, changes


def process_file(filepath: Path, dry_run: bool = False) -> list[tuple[str, str]]:
    """
    Process a single template file.
    
    Args:
        filepath: Path to the template file
        dry_run: If True, don't make changes, just report what would change
    
    Returns:
        List of (old_route, new_route) changes made
    """
    # Read the file
    content = filepath.read_text(encoding='utf-8')
    
    # Update url_for calls
    updated_content, changes = update_url_for_calls(content)
    
    if changes and not dry_run:
        # Create backup
        backup_path = filepath.with_suffix(filepath.suffix + '.backup')
        filepath.rename(backup_path)
        
        # Write updated content
        filepath.write_text(updated_content, encoding='utf-8')
    
    return changes


def main():
    """Main entry point."""
    # Check for --dry-run flag
    dry_run = '--dry-run' in sys.argv
    
    # Find templates directory
    # Try common locations
    for templates_path in ['templates', 'src/templates', '../templates']:
        templates_dir = Path(templates_path)
        if templates_dir.exists():
            break
    else:
        print("❌ Could not find templates directory!")
        print("   Make sure you run this script from your project root.")
        sys.exit(1)
    
    print("=" * 60)
    print("Template URL Migration Script")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("📝 LIVE MODE - Files will be updated (backups created)\n")
    
    # Find all template files
    template_files = find_template_files(templates_dir)
    print(f"Found {len(template_files)} template file(s)\n")
    
    # Process each file
    total_changes = 0
    files_changed = 0
    
    for filepath in template_files:
        changes = process_file(filepath, dry_run)
        
        if changes:
            files_changed += 1
            total_changes += len(changes)
            
            # Print changes for this file
            relative_path = filepath.relative_to(templates_dir)
            print(f"📄 {relative_path}")
            for old_route, new_route in changes:
                print(f"   '{old_route}' → '{new_route}'")
            print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Files scanned:  {len(template_files)}")
    print(f"Files changed:  {files_changed}")
    print(f"Total changes:  {total_changes}")
    
    if dry_run:
        print("\n💡 Run without --dry-run to apply these changes")
    elif files_changed > 0:
        print("\n✅ Changes applied! Backup files created with .backup extension")
        print("   Test your app, then delete .backup files when satisfied")
    else:
        print("\n✅ No changes needed - templates already up to date!")


if __name__ == '__main__':
    main()