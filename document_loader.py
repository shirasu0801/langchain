"""Document loading and processing module."""

import os
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


def load_pdf(file_path: str) -> List[Document]:
    """Load a PDF file and return documents."""
    loader = PyPDFLoader(file_path)
    return loader.load()


def load_text(file_path: str) -> List[Document]:
    """Load a text file and return documents."""
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _get_site_selectors(domain: str) -> List[str]:
    """Get site-specific CSS selectors for content extraction."""
    selectors = {
        # Tech blogs
        'qiita.com': ['div.it-MdContent', 'section.it-MdContent', '#personal-public-article-body'],
        'zenn.dev': ['div.znc', 'article'],
        'note.com': ['div.note-common-styles__textnote-body', 'article'],
        'hatenablog': ['div.entry-content'],
        'medium.com': ['article'],

        # Cloud providers
        'docs.aws.amazon.com': ['#main-col-body', '.awsdocs-content', '#main-content'],
        'learn.microsoft.com': ['#main-column', '.content', 'main'],
        'docs.microsoft.com': ['#main-column', '.content', 'main'],
        'cloud.google.com': ['article.devsite-article', '.devsite-article-body'],
        'docs.oracle.com': ['.content-inner', '#content', 'article'],

        # Programming languages
        'docs.python.org': ['.body', '.document', '#content'],
        'go.dev': ['article', '.Documentation-content', 'main'],
        'doc.rust-lang.org': ['#content', 'main'],
        'nodejs.org': ['#column2', 'article', 'main'],
        'developer.mozilla.org': ['#content', 'article', 'main'],

        # Frameworks & Libraries
        'react.dev': ['article', 'main'],
        'vuejs.org': ['.content', 'main'],
        'angular.io': ['.content', 'article'],
        'nextjs.org': ['article', 'main'],
        'flask.palletsprojects.com': ['.body', '.document'],
        'docs.djangoproject.com': ['#docs-content', '.document'],
        'fastapi.tiangolo.com': ['.md-content', 'article'],

        # Others
        'github.com': ['.markdown-body', 'article'],
        'stackoverflow.com': ['.question', '.answer', '#content'],
        'wikipedia.org': ['#mw-content-text', '#content'],
    }

    for key, value in selectors.items():
        if key in domain:
            return value

    return []


def _extract_with_beautifulsoup(html: str, url: str) -> Optional[str]:
    """Extract content using BeautifulSoup with site-specific selectors."""
    soup = BeautifulSoup(html, 'html.parser')
    domain = urlparse(url).netloc.lower()

    # Remove unwanted elements
    for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                              'aside', 'noscript', 'iframe', 'svg']):
        tag.decompose()

    # Remove common navigation/sidebar classes
    for selector in ['.sidebar', '.navigation', '.nav', '.menu', '.toc',
                     '.breadcrumb', '.pagination', '.comments', '.related',
                     '#sidebar', '#navigation', '#nav', '#menu', '#toc']:
        for element in soup.select(selector):
            element.decompose()

    content = None

    # Try site-specific selectors first
    site_selectors = _get_site_selectors(domain)
    for selector in site_selectors:
        if selector.startswith('.') or selector.startswith('#'):
            element = soup.select_one(selector)
        else:
            element = soup.find(selector)
        if element:
            content = element.get_text(separator='\n')
            break

    # Try generic selectors
    if not content:
        generic_selectors = ['article', 'main', '[role="main"]',
                            '.post-content', '.article-content', '.entry-content',
                            '.content', '.main-content', '#content', '#main']
        for selector in generic_selectors:
            if selector.startswith('.') or selector.startswith('#') or selector.startswith('['):
                element = soup.select_one(selector)
            else:
                element = soup.find(selector)
            if element:
                text = element.get_text(separator='\n')
                if len(text) > 200:  # Minimum content threshold
                    content = text
                    break

    # Final fallback: body
    if not content:
        body = soup.find('body')
        if body:
            content = body.get_text(separator='\n')

    return _clean_text(content) if content else None


def _extract_with_trafilatura(html: str, url: str) -> Optional[str]:
    """Extract content using trafilatura."""
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_images=False,
        include_links=False,
        output_format='txt',
        favor_precision=False,
        favor_recall=True,  # Get more content
    )
    return _clean_text(content) if content else None


def _get_page_title(html: str) -> str:
    """Extract page title from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Try og:title first
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()

    # Try title tag
    title = soup.find('title')
    if title:
        return title.get_text().strip()

    # Try h1
    h1 = soup.find('h1')
    if h1:
        return h1.get_text().strip()

    return ""


def load_url(url: str) -> List[Document]:
    """Load content from a URL using multiple extraction methods."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    # Detect encoding
    if response.encoding == 'ISO-8859-1':
        response.encoding = response.apparent_encoding

    html = response.text
    title = _get_page_title(html) or url

    # Try trafilatura first (generally better for most sites)
    content = _extract_with_trafilatura(html, url)

    # Fallback to BeautifulSoup if trafilatura returns too little content
    if not content or len(content) < 100:
        bs_content = _extract_with_beautifulsoup(html, url)
        if bs_content and len(bs_content) > len(content or ""):
            content = bs_content

    if not content or len(content) < 50:
        raise ValueError(f"Could not extract sufficient content from URL: {url}")

    doc = Document(
        page_content=content,
        metadata={
            "source": url,
            "title": title
        }
    )

    return [doc]


def load_document(file_path: str) -> List[Document]:
    """Load a document based on its file extension."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in [".txt", ".md"]:
        return load_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def split_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[Document]:
    """Split documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""]
    )
    return text_splitter.split_documents(documents)


def process_uploaded_file(uploaded_file, save_dir: str = "data") -> List[Document]:
    """Process an uploaded file from Streamlit."""
    os.makedirs(save_dir, exist_ok=True)

    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    documents = load_document(file_path)
    return split_documents(documents)


def process_url(url: str) -> List[Document]:
    """Process a URL and return chunked documents."""
    documents = load_url(url)
    return split_documents(documents)
