import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytower",
    version="0.0.1",
    author="Mario Belledonne",
    author_email="mbelledonne@gmail.com",
    description="Create, simulate, and render blockworld",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages = ['pytower'],
    entry_points = {
        'console_scripts' : [
            'list-config = pytower.utils:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
