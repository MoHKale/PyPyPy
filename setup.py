import setuptools

with open('README.md', 'r') as File:
    long_description = File.read() 

setuptools.setup(
    name='request_mixin',
    version='0.0.5',
    author='Mohkale',
    auther_email='Mohkalsin@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/MoHKale/PyPyPy',
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
