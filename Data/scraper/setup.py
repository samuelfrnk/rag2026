
import setuptools


NAME = "gather_arxiv_data"
VERSION = "0.1.0"
REQUIRED_PACKAGES = [
    "apache_beam==2.32.0",
    "pandas==1.3.2",
    "arxiv==1.4.2",
    "google_cloud_storage==1.42.1",
]


setuptools.setup(
    name=NAME,
    version=VERSION,
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
    include_package_data=True,
)
