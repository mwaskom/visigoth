from setuptools import setup


DISTNAME = "visigoth"
DESCRIPTION = "Psychophysics experiment control"
MAINTAINER = "Michael Waskom"
MAINTAINER_EMAIL = "mwaskom@nyu.edu"
LICENSE = "BSD (3-clause)"
ZIP_SAFE = False
DOWNLOAD_URL = "https://github.com/mwaskom/visigoth"
VERSION = "0.1.dev"

INSTALL_REQUIRES = ["colorspacious"]

SCRIPTS = ["scripts/visigoth", "scripts/visigoth-remote"]
PACKAGES = ["visigoth", "visigoth.stimuli", "visigoth.ext"]


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
        install_requires=INSTALL_REQUIRES,
        include_package_data=True

    )
