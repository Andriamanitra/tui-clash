from setuptools import setup

setup(
    name="tui-clash",
    version="0.0.1",
    url="https://github.com/Andriamanitra/tui-clash",
    classifiers=[
        "Environment :: Console",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=["textual"],
    packages=["tui_clash"],
    package_dir={"tui_clash": "client"},
    package_data={"tui_clash": ["style.css"]},
    entry_points={
        "console_scripts": [
            "tui-clash = tui_clash.client:main",
        ],
    },
)
