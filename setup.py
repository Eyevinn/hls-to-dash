from setuptools import setup

setup(
    name = "hls2dash",
    version = "0.1.0",
    author = "Jonas Birme",
    author_email = "jonas.birme@eyevinn.se",
    description = ("Command line tools for HLS to MPEG DASH repackaging"),
    license = "MIT",
    url = "https://github.com/Eyevinn/hls-to-dash",
    packages = ['python', 'python/lib'],
    scripts = ['bin/hls-to-dash']
)
