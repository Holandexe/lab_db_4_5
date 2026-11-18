from setuptools import setup, find_packages

setup(
    name="tickets_ua_backend",
    version="1.0.0",
    description="Back-End (Flask + MySQL) для бази даних tickets.ua",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=["Flask>=3.0", "PyMySQL>=1.1", "PyYAML>=6.0", "cryptography>=42.0"],
    python_requires=">=3.10",
)
