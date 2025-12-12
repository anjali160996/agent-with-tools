"""
Custom HTTP tool for fetching content from URLs.
"""
try:
    from langchain.tools import tool
except ImportError:
    # Fallback for different LangChain versions
    from langchain_core.tools import tool
import requests


@tool
def fetch_url_content(url: str) -> str:
    """
    Fetches the content from a given URL.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The text content of the URL, or an error message if the request fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Try to get text content
        content = response.text
        
        # Limit content length to avoid token limits
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[Content truncated due to length]"
            
        return f"Content from {url}:\n\n{content}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL {url}: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

