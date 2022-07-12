from setuptools import setup, find_packages


def scm_version():
    def local_scheme(version):
        if version.tag and not version.distance:
            return version.format_with("")
        else:
            return version.format_choice("+{node}", "+{node}.dirty")
    return {
        "relative_to": __file__,
        "version_scheme": "guess-next-dev",
        "local_scheme": local_scheme
    }


setup(
    name="amaranth-twstft",
    use_scm_version=scm_version(),
    description="Using Amaranth to implement TWSTFT Signal generation",
    license="GPL",
    setup_requires=["setuptools_scm"],
    install_requires=["amaranth"],
    packages=find_packages(),
    project_urls={
        "Source Code": "https://github.com/oscimp/amaranth_twstft",
        "Bug Tracker": "https://github.com/oscimp/amaranth_twstft/issues",
    },
)


