from setuptools import find_packages, setup

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="freshrss_api",
    version="2.0.0",
    description="Easy to use python api to get data from FreshRSS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiswillbeyourgithub/freshrss_python_api/",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    license="GPLv3",
    keywords=[
        "rss",
        "freshrss",
        "python",
        "api",
        "feeds",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests >= 2.32.3",  # pdf with table support
    ],
    extra_require={
        "dev": [
            "pytest >= 8.3.4",
            "build",
            "twine",
        ],
    },
)
