# coding=utf-8
import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bottle_sitemap",
    version="0.1.0",
    author="Manolis Tsoukalas",
    author_email="emmtsoukalas@gmail.com",
    description="Plugin for generating a sitemap in Bottle web framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/m19t12/bottle-sitemap",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
