from setuptools import setup, find_packages

setup(
    name="rosbuddy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.0.0",
    ],
    entry_points={
        'console_scripts': [
            'rosbuddy=rosbuddy.main_app:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A modern, visual ROS 2 development environment",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rosbuddy",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 