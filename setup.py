from setuptools import setup, find_packages
import os

def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ic50_tool_aphane', # The name used for 'pip install' - make it unique!
    version='0.1.0',        # Start with version 0.1.0
    author='Tshepo Aphane',
    author_email='your_email@example.com', # IMPORTANT: Change this to your email!
    description='A Python tool for IC50/EC50 analysis from dose-response data.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/athirstforknowledge/IC50-analysis',
    packages=find_packages(exclude=['tests']), # Automatically finds 'ic50_pkg'
    install_requires=parse_requirements('requirements.txt'), # Reads from your requirements file
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    python_requires='>=3.7',
    # We might add entry points later if we make a command-line tool
)