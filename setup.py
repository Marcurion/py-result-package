from setuptools import setup, find_packages

setup(
    name="resolute",            # Your package name
    version="1.0.3",                # Version of the package
    author="Marcurion",           # Author name
    author_email="marcurion@private.com",  # Author email
    description="Implementation of the Result pattern similar to C# ErrorOr package",
    long_description=open('README.md').read(),  # Optional: read from README.md
    long_description_content_type='text/markdown',  # Specify markdown if used
    url="https://github.com/Marcurion/py-result-package",    # Optional: Project's URL, if available
    packages=find_packages(),     # Automatically find packages in this directory
    package_data={"resolute": ["py.typed"]},
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": ["pytest"]
    },
    python_requires='>=3.13.0',      # Minimum version of Python
)

