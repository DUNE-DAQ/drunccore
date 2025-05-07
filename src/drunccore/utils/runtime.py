import os

from drunccore.exceptions import DruncSetupException


def get_version():
    version = os.getenv("DUNE_DAQ_BASE_RELEASE")
    if not version:
        raise DruncSetupException(
            "Utils: dunedaq version not in the variable env DUNE_DAQ_BASE_RELEASE! Exit drunc and\nexport DUNE_DAQ_BASE_RELEASE=dunedaq-vX.XX.XX\n"
        )
    return version


def get_releases_dir():
    releases_dir = os.getenv("SPACK_RELEASES_DIR")
    if not releases_dir:
        raise DruncSetupException(
            "Utils: cannot get env SPACK_RELEASES_DIR! Exit drunc and\nrun dbt-workarea-env or dbt-setup-release."
        )
    return releases_dir


def release_or_dev():
    is_release = os.getenv("DBT_SETUP_RELEASE_SCRIPT_SOURCED")
    if is_release:
        return "rel"
    is_devenv = os.getenv("DBT_WORKAREA_ENV_SCRIPT_SOURCED")
    if is_devenv:
        return "dev"
    return "rel"


def get_rte_script():
    script = ""
    if release_or_dev() == "rel":
        ver = get_version()
        releases_dir = get_releases_dir()
        script = os.path.join(releases_dir, ver, "daq_app_rte.sh")

    else:
        dbt_install_dir = os.getenv("DBT_INSTALL_DIR")
        script = os.path.join(dbt_install_dir, "daq_app_rte.sh")

    if not os.path.exists(script):
        raise DruncSetupException(
            f"Couldn't understand where to find the rte script tentative: {script}"
        )
    return script
