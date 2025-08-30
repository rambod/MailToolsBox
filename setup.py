from setuptools import setup, find_packages
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

setup(
    name="MailToolsBox",
    version="1.1.0",
    description="Modern sync and async SMTP with optional TLS/SSL, OAuth2 XOAUTH2, Jinja2 templates, and attachments.",
    long_description=README,
    long_description_content_type="text/markdown",
    license="MIT",
    author="Rambod Ghashghai",
    author_email="gh.rambod@gmail.com",
    url="https://github.com/rambod/MailToolsBox",
    download_url="https://github.com/rambod/MailToolsBox/archive/refs/tags/v1.1.0.tar.gz",
    packages=find_packages(exclude=("tests", "examples")),
    include_package_data=True,  # needed with package_data to ship templates
    package_data={
        # adjust the package key to your actual package name if different
        "MailToolsBox": ["templates/*", "templates/**/*"],
    },
    install_requires=[
        "Jinja2>=3.0.2",
        "email-validator>=2.0.0",
        "aiosmtplib>=2.0.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.20",
            "mypy>=1.0",
            "black>=24.0",
            "ruff>=0.5",
        ],
        "docs": [
            "mkdocs>=1.5",
            "mkdocs-material>=9.5",
        ],
    },
    keywords=[
        "mail",
        "smtp",
        "email",
        "tls",
        "ssl",
        "oauth2",
        "xoauth2",
        "jinja2",
        "asyncio",
        "aiosmtplib",
        "email-validation",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Email",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    project_urls={
        "Source": "https://github.com/rambod/MailToolsBox",
        "Issues": "https://github.com/rambod/MailToolsBox/issues",
    },
)
