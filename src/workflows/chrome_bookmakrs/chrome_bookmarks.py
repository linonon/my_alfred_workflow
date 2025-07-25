import json
import os
import platform
import sys
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple


try:
    # Add project root to path
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from helpers.alfred import AlfredScriptFilter, AlfredItem, AlfredMod

except ImportError:
    sys.exit(
        "Error: Could not import Alfred models. Ensure the project structure is correct."
    )


try:
    from pypinyin import lazy_pinyin

    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

    def lazy_pinyin(hans):
        return []

# >>> lazy_pinyin('中心')  # 不考虑多音字的情况
# ['zhong', 'xin']


# Custom exceptions for better error handling
class ChromeBookmarksError(Exception):
    """Base exception for Chrome bookmarks errors."""
    pass


class ChromeNotInstalledError(ChromeBookmarksError):
    """No Chrome installation found."""
    pass


class ProfileNotFoundError(ChromeBookmarksError):
    """Profile directory not found."""
    pass


class BookmarksNotFoundError(ChromeBookmarksError):
    """Bookmarks file not found or inaccessible."""
    pass


class BookmarksCorruptedError(ChromeBookmarksError):
    """Bookmarks file exists but contains invalid JSON."""
    pass


def debug_log(message: str) -> None:
    """Log debug information if debug mode is enabled."""
    if os.environ.get("CHROME_BOOKMARKS_DEBUG", "").lower() in ("1", "true", "yes"):
        print(f"[DEBUG] {message}", file=sys.stderr)


def get_chrome_variants_by_os() -> List[Tuple[str, str]]:
    """Get Chrome variant paths for the current OS, ordered by preference.
    
    Returns:
        List of (variant_name, relative_path) tuples
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return [
            ("Google Chrome", "Library/Application Support/Google/Chrome"),
            ("Chromium", "Library/Application Support/Chromium"),
            ("Google Chrome Beta", "Library/Application Support/Google/Chrome Beta"),
            ("Google Chrome Dev", "Library/Application Support/Google/Chrome Dev"),
            ("Google Chrome Canary", "Library/Application Support/Google/Chrome Canary"),
        ]
    elif system == "Windows":
        return [
            ("Google Chrome", "Google/Chrome/User Data"),
            ("Chromium", "Chromium/User Data"),
            ("Google Chrome Beta", "Google/Chrome Beta/User Data"),
            ("Google Chrome Dev", "Google/Chrome Dev/User Data"),
            ("Google Chrome Canary", "Google/Chrome SxS/User Data"),
        ]
    elif system == "Linux":
        return [
            ("Google Chrome", ".config/google-chrome"),
            ("Chromium", ".config/chromium"),
            ("Google Chrome Beta", ".config/google-chrome-beta"),
            ("Google Chrome Dev", ".config/google-chrome-unstable"),
        ]
    else:
        raise OSError(f"Unsupported operating system: {system}")


def find_chrome_installations() -> List[Tuple[str, Path]]:
    """Find all available Chrome installations.
    
    Returns:
        List of (variant_name, chrome_directory) tuples for existing installations
    """
    installations = []
    variants = get_chrome_variants_by_os()
    
    for variant_name, relative_path in variants:
        if platform.system() == "Windows":
            chrome_dir = Path(os.environ["LOCALAPPDATA"]) / relative_path
        else:
            chrome_dir = Path.home() / relative_path
            
        if chrome_dir.exists():
            debug_log(f"Found {variant_name} at: {chrome_dir}")
            installations.append((variant_name, chrome_dir))
        else:
            debug_log(f"{variant_name} not found at: {chrome_dir}")
    
    return installations


def validate_profile_bookmarks(profile_path: Path) -> bool:
    """Validate that a profile has accessible bookmarks.
    
    Args:
        profile_path: Path to the profile directory
        
    Returns:
        True if bookmarks are accessible and valid, False otherwise
    """
    bookmarks_file = profile_path / "Bookmarks"
    
    if not bookmarks_file.exists():
        debug_log(f"Bookmarks file not found: {bookmarks_file}")
        return False
        
    try:
        with open(bookmarks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Basic validation - check for expected structure
        if "roots" not in data:
            debug_log(f"Invalid bookmarks structure in: {bookmarks_file}")
            return False
            
        debug_log(f"Valid bookmarks found in: {bookmarks_file}")
        return True
        
    except (json.JSONDecodeError, IOError, OSError) as e:
        debug_log(f"Error validating bookmarks in {bookmarks_file}: {e}")
        return False


def get_profile_bookmark_count(profile_path: Path) -> int:
    """Get the number of bookmarks in a profile (for prioritization).
    
    Args:
        profile_path: Path to the profile directory
        
    Returns:
        Number of bookmarks, or 0 if unable to count
    """
    try:
        bookmarks = get_chrome_bookmarks_from_path(profile_path / "Bookmarks")
        return len(bookmarks)
    except Exception:
        return 0


def find_best_profile_in_installation(chrome_dir: Path, preferred_profile: Optional[str] = None) -> Optional[str]:
    """Find the best available profile in a Chrome installation.
    
    Args:
        chrome_dir: Path to Chrome installation directory
        preferred_profile: Preferred profile name if specified
        
    Returns:
        Profile name if found, None otherwise
    """
    debug_log(f"Searching for profiles in: {chrome_dir}")
    
    # If preferred profile is specified and valid, use it
    if preferred_profile:
        preferred_path = chrome_dir / preferred_profile
        if preferred_path.exists() and validate_profile_bookmarks(preferred_path):
            debug_log(f"Using preferred profile: {preferred_profile}")
            return preferred_profile
        else:
            debug_log(f"Preferred profile '{preferred_profile}' not found or invalid")
    
    # Try "Default" profile (most common)
    default_path = chrome_dir / "Default"
    if default_path.exists() and validate_profile_bookmarks(default_path):
        debug_log("Using Default profile")
        return "Default"
    
    # Scan all available profiles and prioritize by bookmark count
    profile_candidates = []
    
    if chrome_dir.exists():
        for item in chrome_dir.iterdir():
            if item.is_dir() and validate_profile_bookmarks(item):
                bookmark_count = get_profile_bookmark_count(item)
                profile_candidates.append((item.name, bookmark_count))
                debug_log(f"Found profile '{item.name}' with {bookmark_count} bookmarks")
    
    if profile_candidates:
        # Sort by bookmark count (descending) and return the best one
        profile_candidates.sort(key=lambda x: x[1], reverse=True)
        best_profile = profile_candidates[0][0]
        debug_log(f"Selected best profile: {best_profile}")
        return best_profile
    
    debug_log("No valid profiles found")
    return None


def find_best_chrome_profile(preferred_profile: Optional[str] = None) -> Tuple[Path, str]:
    """Find the best Chrome installation and profile.
    
    Args:
        preferred_profile: Preferred profile name if specified
        
    Returns:
        Tuple of (chrome_directory, profile_name)
        
    Raises:
        ChromeNotInstalledError: If no Chrome installation is found
        ProfileNotFoundError: If no valid profiles are found
    """
    installations = find_chrome_installations()
    
    if not installations:
        raise ChromeNotInstalledError("No Chrome installations found")
    
    # Try each installation in order of preference
    for variant_name, chrome_dir in installations:
        debug_log(f"Checking {variant_name} installation")
        profile = find_best_profile_in_installation(chrome_dir, preferred_profile)
        
        if profile:
            debug_log(f"Selected {variant_name} with profile '{profile}'")
            return chrome_dir, profile
    
    raise ProfileNotFoundError("No valid profiles found in any Chrome installation")


def get_chrome_bookmarks_path(chrome_dir: Path, profile: str) -> Path:
    """Get Chrome bookmarks file path for a specific installation and profile.
    
    Args:
        chrome_dir: Path to Chrome installation directory
        profile: Profile name
        
    Returns:
        Path to the bookmarks file
    """
    return chrome_dir / profile / "Bookmarks"


def list_all_chrome_profiles() -> List[Tuple[str, str, str]]:
    """List all available Chrome profiles across all installations.
    
    Returns:
        List of (variant_name, profile_name, profile_path) tuples
    """
    all_profiles = []
    installations = find_chrome_installations()
    
    for variant_name, chrome_dir in installations:
        if chrome_dir.exists():
            for item in chrome_dir.iterdir():
                if item.is_dir() and validate_profile_bookmarks(item):
                    all_profiles.append((variant_name, item.name, str(item)))
    
    return sorted(all_profiles)


def extract_bookmarks(
    bookmark_node: Dict[str, Any], bm: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Recursively extract bookmarks from the bookmark tree."""
    if bm is None:
        bm = []

    if bookmark_node.get("type") == "url":
        bm.append(
            {
                "name": bookmark_node.get("name", ""),
                "url": bookmark_node.get("url", ""),
                "date_added": bookmark_node.get("date_added", ""),
                "date_modified": bookmark_node.get("date_modified", ""),
            }
        )
    elif bookmark_node.get("type") == "folder" and "children" in bookmark_node:
        for child in bookmark_node["children"]:
            extract_bookmarks(child, bm)

    return bm


def get_chrome_bookmarks_from_path(bookmarks_path: Path) -> List[Dict[str, Any]]:
    """Get all bookmarks from a specific bookmarks file.
    
    Args:
        bookmarks_path: Path to the bookmarks file
        
    Returns:
        List of bookmark dictionaries
        
    Raises:
        BookmarksNotFoundError: If bookmarks file doesn't exist
        BookmarksCorruptedError: If bookmarks file contains invalid JSON
    """
    if not bookmarks_path.exists():
        raise BookmarksNotFoundError(f"Chrome bookmarks file not found at: {bookmarks_path}")

    try:
        with open(bookmarks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_bookmarks = []

        # Extract bookmarks from bookmark bar
        if "roots" in data and "bookmark_bar" in data["roots"]:
            extract_bookmarks(data["roots"]["bookmark_bar"], all_bookmarks)

        # Extract bookmarks from other bookmarks
        if "roots" in data and "other" in data["roots"]:
            extract_bookmarks(data["roots"]["other"], all_bookmarks)

        # Extract bookmarks from mobile bookmarks (if exists)
        if "roots" in data and "synced" in data["roots"]:
            extract_bookmarks(data["roots"]["synced"], all_bookmarks)

        debug_log(f"Extracted {len(all_bookmarks)} bookmarks from {bookmarks_path}")
        return all_bookmarks

    except json.JSONDecodeError as e:
        raise BookmarksCorruptedError(f"Invalid JSON in bookmarks file: {e}") from e
    except Exception as e:
        raise BookmarksNotFoundError(f"Error reading bookmarks: {e}") from e


def get_chrome_bookmarks(chrome_dir: Path, profile: str) -> List[Dict[str, Any]]:
    """Get all bookmarks from Chrome for a specific installation and profile.
    
    Args:
        chrome_dir: Path to Chrome installation directory
        profile: Profile name
        
    Returns:
        List of bookmark dictionaries
    """
    bookmarks_path = get_chrome_bookmarks_path(chrome_dir, profile)
    return get_chrome_bookmarks_from_path(bookmarks_path)


def search_bookmarks(
    bookmarks: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """Search bookmarks and return scored results."""
    if not query:
        return bookmarks[:10]  # Return first 10 if no query

    scored_bookmarks = []
    query_lower = query.lower()

    for bookmark in bookmarks:
        score = 0
        name = bookmark["name"].lower()
        if HAS_PYPINYIN:
            name = name + "".join(lazy_pinyin(name))
        url = bookmark["url"].lower()

        # Name exact match gets highest score
        if query_lower == name:
            score += 1000
        # Name contains query gets high score
        elif query_lower in name:
            score += 500
        # URL contains query gets medium score
        elif query_lower in url:
            score += 200
        # Fuzzy match on name
        else:
            name_ratio = SequenceMatcher(None, query_lower, name).ratio()
            if name_ratio > 0.3:
                score += int(name_ratio * 100)

        if score > 0:
            bookmark_copy = bookmark.copy()
            bookmark_copy["score"] = score
            scored_bookmarks.append(bookmark_copy)

    # Sort by score descending
    scored_bookmarks.sort(key=lambda x: x["score"], reverse=True)
    return scored_bookmarks[:10]  # Return top 10


def print_bookmarks(bm: List[Dict[str, Any]]):
    """Print bookmarks in a readable format."""
    print(f"Found {len(bm)} bookmarks:\n")

    for i, bookmark in enumerate(bm, 1):
        print(f"{i}. {bookmark['name']}")
        print(f"   URL: {bookmark['url']}")
        print(f"   Added: {bookmark['date_added']}")
        print("-" * 80)


def save_bookmarks_to_file(bm: List[Dict[str, Any]], file: str = "bookmarks.json"):
    """Save bookmarks to a JSON file."""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(bm, f, ensure_ascii=False, indent=2)
    print(f"Bookmarks saved to {file}")


def output_alfred_format(bookmarks: List[Dict[str, Any]], query: str = ""):
    """Output bookmarks in Alfred workflow format."""
    # Search and score bookmarks
    filtered_bookmarks = search_bookmarks(bookmarks, query)

    script_filter = AlfredScriptFilter()

    for bookmark in filtered_bookmarks:
        mods = {
            "cmd": AlfredMod(
                valid=True, arg=bookmark["url"], subtitle="Copy URL to clipboard"
            ),
            "alt": AlfredMod(
                valid=True,
                arg=bookmark["name"],
                subtitle="Copy bookmark name to clipboard",
            ),
        }

        item = AlfredItem(
            title=bookmark["name"],
            subtitle=bookmark["url"],
            arg=bookmark["url"],
            mods=mods,
        )
        script_filter.add_item(item)

    # If no results found
    if not script_filter.items:
        script_filter.add_simple_item(
            title="No bookmarks found", subtitle="Try a different search term"
        ).valid = False

    print(script_filter.to_json())


def create_error_output(title: str, subtitle: str, debug_info: str = "") -> None:
    """Create Alfred error output with optional debug information.
    
    Args:
        title: Error title
        subtitle: Error subtitle  
        debug_info: Optional debug information
    """
    script_filter = AlfredScriptFilter()
    
    # Main error item
    script_filter.add_simple_item(title=title, subtitle=subtitle).valid = False
    
    # Add debug info if available and debug mode is enabled
    if debug_info and os.environ.get("CHROME_BOOKMARKS_DEBUG"):
        script_filter.add_simple_item(
            title="Debug Info", 
            subtitle=debug_info[:100] + "..." if len(debug_info) > 100 else debug_info
        ).valid = False
    
    print(script_filter.to_json())


def main():
    # Get search query from command line
    query = sys.argv[1] if len(sys.argv) > 1 else ""

    # Get preferred profile from environment variable
    preferred_profile = os.environ.get("CHROME_PROFILE")
    debug_log(f"Preferred profile from environment: {preferred_profile or 'None'}")
    debug_log(f"Search query: '{query}'")

    try:
        # Find the best Chrome installation and profile
        chrome_dir, profile = find_best_chrome_profile(preferred_profile)
        debug_log(f"Selected Chrome directory: {chrome_dir}")
        debug_log(f"Selected profile: {profile}")

        # Get bookmarks and output in Alfred format
        bookmarks = get_chrome_bookmarks(chrome_dir, profile)
        debug_log(f"Found {len(bookmarks)} bookmarks")
        output_alfred_format(bookmarks, query)

    except ChromeNotInstalledError:
        create_error_output(
            title="Chrome Not Found",
            subtitle="No Chrome installation detected. Install Chrome or Chromium.",
            debug_info="Searched for: Google Chrome, Chromium, Chrome Beta, Chrome Dev"
        )
        
    except ProfileNotFoundError:
        installations = find_chrome_installations()
        installation_names = [name for name, _ in installations]
        create_error_output(
            title="No Chrome Profiles Found",
            subtitle=f"No valid profiles in {', '.join(installation_names)}",
            debug_info=f"Searched installations: {installation_names}"
        )
        
    except (BookmarksNotFoundError, BookmarksCorruptedError) as e:
        create_error_output(
            title="Bookmarks Error",
            subtitle="Bookmarks file not found or corrupted",
            debug_info=str(e)
        )
        
    except Exception as e:
        create_error_output(
            title="Unexpected Error",
            subtitle="An unexpected error occurred",
            debug_info=f"{type(e).__name__}: {e}"
        )


if __name__ == "__main__":
    main()
