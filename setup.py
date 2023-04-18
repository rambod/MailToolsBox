from distutils.core import setup


setup(
    name='MailToolsBox',
    packages=['MailToolsBox'],
    version='0.1.0.2',
    license='MIT',
    # Give a short description about your library
    description='Mail tools simplify mail server and sender development for developers.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='Rambod Ghashghai',                   # Type in your name
    author_email='gh.rambod@gmail.com',      # Type in your E-Mail
    # Provide either the link to your github or to your website
    url='https://www.rambod.net',
    # I explain this later on
    download_url='https://github.com/rambod/MailToolsBox/archive/0.0.4.6.tar.gz',
    keywords=['Mail', 'Server', 'smtp',  'send', 'email', 'tools',
              'box'],   # Keywords that define your package best
    install_requires=[
        "Jinja2==3.0.2",
    ],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 4 - Beta',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        'Programming Language :: Python :: 3.11',
    ],
)
