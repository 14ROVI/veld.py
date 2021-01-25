import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="veld.py",
    version="0.0.1",
    author="14ROVI",
    author_email="",
    description="An easy to use API wrapper for veld.chat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/14ROVI/veld.py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)