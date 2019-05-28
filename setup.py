from setuptools import setup
import versioneer


DISTNAME = "visigoth"
DESCRIPTION = "Psychophysics experiment control"
MAINTAINER = "Michael Waskom"
MAINTAINER_EMAIL = "mwaskom@nyu.edu"
LICENSE = "BSD (3-clause)"
ZIP_SAFE = False
DOWNLOAD_URL = "https://github.com/mwaskom/visigoth"

INSTALL_REQUIRES = ["colorspacious"]

SCRIPTS = [
    "scripts/visigoth",
    "scripts/visigoth-remote",
    "scripts/visigoth-screencheck"
]
PACKAGES = ["visigoth", "visigoth.stimuli", "visigoth.ext"]

INCLUDE_PACKAGE_DATA = True

VERSION = versioneer.get_version()
CMDCLASS = versioneer.get_cmdclass()


if __name__ == "__main__":

    setup(

        name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        license=LICENSE,
        download_url=DOWNLOAD_URL,
        install_requires=INSTALL_REQUIRES,
        zip_safe=ZIP_SAFE,
        scripts=SCRIPTS,
        packages=PACKAGES,
        include_package_data=INCLUDE_PACKAGE_DATA,
        version=VERSION,
        cmdclass=CMDCLASS,

    )
