from setuptools import setup, find_packages

setup(
    name="result",            # Your package name
    version="0.9.1",                # Version of the package
    author="Marcurion",           # Author name
    author_email="marcurion@private",  # Author email
    description="Implementation of the Result pattern similar to C# ErrorOr package",
    long_description=open('README.md').read(),  # Optional: read from README.md
    long_description_content_type='text/markdown',  # Specify markdown if used
    url="",    # Optional: Project's URL, if available
    packages=find_packages(),     # Automatically find packages in this directory
    install_requires=[],          # List of dependencies (can leave empty for local use)
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": ["pytest"]
    },
    python_requires='>=3.11.11',      # Minimum version of Python
)

