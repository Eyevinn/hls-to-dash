from os.path import dirname, abspath, join, exists
from setuptools import setup

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

long_description = None
if exists("README.md"):
    long_description = read_md("README.md")

install_reqs = [req for req in open(abspath(join(dirname(__file__), 'requirements.txt')))]

setup(
    name = "hls2dash",
    version = "0.2.1",
    author = "Jonas Birme",
    author_email = "jonas.birme@eyevinn.se",
    description = "Command line tools for HLS to MPEG DASH repackaging",
    long_description=long_description,
    license = "MIT",
    install_requires=install_reqs,
    url = "https://github.com/Eyevinn/hls-to-dash",
    packages = ['hls2dash', 'hls2dash/lib', 'hls2dash/tsremux'],
    entry_points = {
        'console_scripts': [
            'hls-to-dash=hls2dash:main',
            'ts-to-fmp4=hls2dash.tsremux:main'
        ]
    }
)
