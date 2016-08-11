from os.path import dirname, abspath, join, exists
from setuptools import setup

install_reqs = [reg for req in open(abspath(join(dirname(__file__), 'requirements.txt')))]

setup(
    name = "hls2dash",
    version = "0.1.0",
    author = "Jonas Birme",
    author_email = "jonas.birme@eyevinn.se",
    description = ("Command line tools for HLS to MPEG DASH repackaging"),
    license = "MIT",
    install_requires=install_reqs,
    url = "https://github.com/Eyevinn/hls-to-dash",
    packages = ['python', 'python/lib'],
    scripts = ['bin/hls-to-dash']
)
