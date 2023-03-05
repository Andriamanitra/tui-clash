from setuptools import Extension, setup

setup(
    name = "tui-clash",
    version = "0.0.1",
    url = "https://github.com/Andriamanitra/tui-clash",
    
    classifiers = [
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],

    python_requires = ">=3.7",
    requires = ["textual"],

    packages = ["tui_clash"],
    package_dir = {'tui_clash': '.'},
    package_data = {'tui_clash': ['style.css']},

    entry_points = {
        # add server too ?
        'console_scripts': [
            'tui-clash = tui_clash.client:main',                  
        ],
    },
)