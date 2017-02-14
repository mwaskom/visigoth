from setuptools import setup


DISTNAME = "visigoth"
DESCRIPTION = "Psychophysics experiment control"
MAINTAINER = "Michael Waskom"
MAINTAINER_EMAIL = "mwaskom@nyu.edu"
LICENSE = "BSD (3-clause)"
ZIP_SAFE = False
DOWNLOAD_URL = "https://github.com/mwaskom/visigoth"
VERSION = "0.1.dev"

SCRIPTS = ["scripts/visigoth", "scripts/visigoth-client"]
PACKAGES = ["visigoth", "visigoth.stimuli", "visigoth.ext"]
PACKAGE_DIR = {"visigoth": "visigoth"}
PACKAGE_DATA = {"visigoth": ["sounds/*.wav"]}


if __name__ == "__main__":

    setup(

        name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        license=LICENSE,
        download_url=DOWNLOAD_URL,
        zip_safe=ZIP_SAFE,
        version=VERSION,
        scripts=SCRIPTS,
        packages=PACKAGES,
        package_dir=PACKAGE_DIR,
        package_data=PACKAGE_DATA,

    )
