import re
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

# Tags that typically contain non-job or boilerplate content
UNWANTED_TAGS = [
    "script", "style", "noscript", "header", "footer", "nav", "aside",
    "svg", "form", "button", "iframe", "object", "embed"
]


def extract_clean_job_text(html_content: str) -> str:
    """
    Parses HTML content, strips non-content tags, extracts readable text,
    normalizes whitespace, and validates that sufficient text content exists.
    """
    if not html_content or not html_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty content received from job posting. Please paste the job description manually."
        )

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove irrelevant tags
    for tag in soup(UNWANTED_TAGS):
        tag.decompose()

    # Prefer common job description containers if present
    possible_containers = [
        soup.find(attrs={"class": re.compile(r"(job-description|description|jobDetail|job-posting|posting-requirements|show-more-less-html)", re.I)}),
        soup.find(attrs={"id": re.compile(r"(job-description|jobDetail|description)", re.I)}),
        soup.find("main"),
        soup.find("article"),
    ]

    target_node = None
    for container in possible_containers:
        if container and len(container.get_text(strip=True)) >= 200:
            target_node = container
            break

    if target_node is None:
        target_node = soup.body if soup.body else soup

    # Extract text with space separators
    text = target_node.get_text(separator="\n")

    # Clean up excess whitespace and consecutive empty lines
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if line]
    cleaned_text = "\n".join(clean_lines)

    # Validate that sufficient text content was extracted (at least 150 characters)
    if len(cleaned_text) < 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The retrieved page does not contain sufficient readable job description text (may be client-rendered with JavaScript or paywalled). Please paste the job description text manually."
        )

    # Restrict maximum extracted text to 40,000 characters to prevent excessive tokens / latency
    if len(cleaned_text) > 40000:
        cleaned_text = cleaned_text[:40000]

    return cleaned_text
