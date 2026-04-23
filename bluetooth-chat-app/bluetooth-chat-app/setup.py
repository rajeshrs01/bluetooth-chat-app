from setuptools import setup, find_packages

setup(
    name="bluechat",
    version="1.0.0",
    description="A Bluetooth chat and voice call app for Python",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "PyBluez",
        "pyaudio",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "bluechat=main:main",
        ]
    },
)
