from setuptools import setup, find_packages

setup(
    name='MailToolsBox',
    packages=find_packages(),
    version='1.0.1',  # Increased version for major revamp
    license='MIT',
    description='A modern and efficient Python library for sending emails with SMTP, Jinja2 templates, and attachments.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author='Rambod Ghashghai',
    author_email='gh.rambod@gmail.com',
    url='https://github.com/rambod/MailToolsBox',
    download_url='https://github.com/rambod/MailToolsBox/archive/refs/tags/v1.0.1.tar.gz',
    keywords=['Mail', 'SMTP', 'email', 'tools', 'attachments', 'Jinja2', 'Python', 'email-validation'],
    install_requires=[
        "Jinja2>=3.0.2",
        "email-validator>=2.0.0",
        "aiosmtplib>=2.0.0"
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
    python_requires=">=3.7"
)
