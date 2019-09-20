from distutils.core import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
  name = 'MailToolsBox',
  packages = ['MailToolsBox'],
  version = '0.0.4.5',
  license='MIT',
  description = 'Mail Tools boxes to make developer life easier on build mail sender or even mail server',   # Give a short description about your library
  long_description=open('README.rst').read(),
  long_description_content_type="text/rst",
  author = 'Rambod Ghashghai',                   # Type in your name
  author_email = 'rambod@ramai.io',      # Type in your E-Mail
  url = 'https://www.ramai.io',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/rambod/MailToolsBox/archive/0.0.4.5.tar.gz',    # I explain this later on
  keywords = ['Mail', 'Server', 'smtp' ,  'send' , 'email', 'tools', 'box'],   # Keywords that define your package best
  install_requires=[
    # I get to this in a second
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Communications :: Email',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)