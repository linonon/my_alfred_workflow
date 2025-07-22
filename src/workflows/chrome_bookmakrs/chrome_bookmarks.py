import json
import os
import platform
import sys
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional


try:
    # Add project root to path
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from models.alfred import AlfredScriptFilter, AlfredItem, AlfredMod

except ImportError:
    sys.exit("Error: Could not import Alfred models. Ensure the project structure is correct.")


try:
    from pypinyin import lazy_pinyin

    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

    def lazy_pinyin(hans):
        return []

# >>> lazy_pinyin('中心')  # 不考虑多音字的情况
# ['zhong', 'xin']


def get_chrome_bookmarks_path(profile: str = "Default") -> Path:
    """Get Chrome bookmarks file path based on the operating system and profile."""
    system = platform.system()

    if system == "Darwin":  # macOS
        path = (
            Path.home()
            / f"Library/Application Support/Google/Chrome/{profile}/Bookmarks"
        )
    elif system == "Windows":
        path = (
            Path(os.environ["LOCALAPPDATA"])
            / f"Google/Chrome/User Data/{profile}/Bookmarks"
        )
    elif system == "Linux":
        path = Path.home() / f".config/google-chrome/{profile}/Bookmarks"
    else:
        raise OSError(f"Unsupported operating system: {system}")

    return path


def list_chrome_profiles() -> List[str]:
    """List available Chrome profiles."""
    system = platform.system()

    if system == "Darwin":  # macOS
        chrome_dir = Path.home() / "Library/Application Support/Google/Chrome"
    elif system == "Windows":
        chrome_dir = Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data"
    elif system == "Linux":
        chrome_dir = Path.home() / ".config/google-chrome"
    else:
        raise OSError(f"Unsupported operating system: {system}")

    profiles = []
    if chrome_dir.exists():
        for item in chrome_dir.iterdir():
            if item.is_dir() and (item / "Bookmarks").exists():
                profiles.append(item.name)

    return sorted(profiles)


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


def get_chrome_bookmarks(profile: str = "Default") -> List[Dict[str, Any]]:
    """Get all bookmarks from Chrome."""
    bookmarks_path = get_chrome_bookmarks_path(profile)

    if not bookmarks_path.exists():
        raise FileNotFoundError(f"Chrome bookmarks file not found at: {bookmarks_path}")

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

        return all_bookmarks

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in bookmarks file: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Error reading bookmarks: {e}") from e


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
                valid=True,
                arg=bookmark["url"],
                subtitle="Copy URL to clipboard"
            ),
            "alt": AlfredMod(
                valid=True,
                arg=bookmark["name"],
                subtitle="Copy bookmark name to clipboard"
            ),
        }
        
        item = AlfredItem(
            title=bookmark["name"],
            subtitle=bookmark["url"],
            arg=bookmark["url"],
            mods=mods
        )
        script_filter.add_item(item)

    # If no results found
    if not script_filter.items:
        script_filter.add_simple_item(
            title="No bookmarks found",
            subtitle="Try a different search term"
        ).valid = False

    print(script_filter.to_json())


def main():
    # Get search query from command line
    query = sys.argv[1] if len(sys.argv) > 1 else ""

    # Get profile from environment variable or use default
    profile = os.environ.get("CHROME_PROFILE", "Profile 1")

    try:
        # Check if profile exists, fallback to first available
        profiles = list_chrome_profiles()
        if not profiles:
            script_filter = AlfredScriptFilter()
            script_filter.add_simple_item(
                title="No Chrome profiles found",
                subtitle="Chrome bookmarks not accessible"
            ).valid = False
            print(script_filter.to_json())
            return

        if profile not in profiles:
            profile = profiles[0]  # Use first available profile

        # Get bookmarks and output in Alfred format
        bookmarks = get_chrome_bookmarks(profile)
        output_alfred_format(bookmarks, query)

    except Exception as e:
        script_filter = AlfredScriptFilter()
        script_filter.add_simple_item(
            title="Error loading bookmarks", 
            subtitle=str(e)
        ).valid = False
        print(script_filter.to_json())


if __name__ == "__main__":
    main()
