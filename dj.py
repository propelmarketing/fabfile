"""
Tyrel Souza <tsouza@propelmarketing.com>
"""
import sys
import os

from fabric.context_managers import shell_env
from fabric.api import local, lcd, task

try:
    from projectconf import DJANGO_PROJECT, ENVIRONMENT_VARIABLES
except:
    DJANGO_PROJECT = None
    ENVIRONMENT_VARIABLES = []


@task
def copy_media():
    """Django: Copies local media to s3"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py sync_media_s3 -p media')


@task
def development():
    """Django: Run Server in Dev Mode"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')


@task
def production():
    """Django: Run server in production mode """
    ENV = _get_env_from_file()
    ENV['DEBUG'] = ''
    ENV['PRODUCTION'] = 'True'
    ENV['STAGING'] = ''
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')


@task
def setup():
    """Django: Setup Environment Variables, then pip install, then syncdb, finally migrate """
    ENV = _do_env_setup()
    cwd = _get_run_directory()
    ENV['CPPFLAGS'] = '-Qunused-arguments'
    ENV['CFLAGS'] = '-Qunused-arguments'

    # Run bash scripts
    if 'scripts' in os.listdir('.') and "setup.sh" in os.listdir('scripts'):
        local('./scripts/setup.sh')
    if 'scripts' in os.listdir('.') and "setup_dev.sh" in os.listdir('scripts'):
        local('./scripts/setup_dev.sh')

    local('pip install -r requirements.txt')
    if os.path.isfile("requirements/local.txt"):
        local('pip install -r requirements/local.txt')

    with shell_env(**ENV):
        with lcd(cwd):
            _local_settings(cwd)
            local('python manage.py syncdb --noinput')
            local('python manage.py migrate')
            if DJANGO_PROJECT == "intake_forms":
                local('python manage.py load_fields')

@task
def local_agency():
    """Django: setup an agency to be used with localhost"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py local_agency')


@task
def shell():
    """Django: Run Shell"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py shell')


@task
def staging():
    """Django: Run server in Staging Mode"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = ''
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')


@task
def superuser():
    """Django: Creates Superuser"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py createsuperuser')


@task
def test():
    """Django: Runs the default tests"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py test')


@task
def update_agencies():
    """Django: Update Agencies"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py update_agencies')


# Private, not picked up by Fabric
def _get_run_directory():
    if not 'manage.py' in os.listdir('.'):
        cwd = DJANGO_PROJECT
    else:
        cwd = '.'
    return cwd


def _local_settings(cwd):
    """
        Copies local_settings.py.default to local_settings.py if needed
        WILL NOT OVERRIDE
    """
    files = os.listdir(cwd)
    if "local_settings.py.default" in files and "local_settings.py" not in files:
        local('cp local_settings.py.default local_settings.py')


def _do_env_setup():
    """ Prompt to see if setup environment, if yes, setup, otherwise get env """
    do_env = raw_input('Setup Environment? (Y/N) ').rstrip("\n")
    if do_env.lower() == "y":
        if not ENVIRONMENT_VARIABLES:
            print "No list 'ENVIRONMENT_VARIABLES' in projectconf.py"
            return
        ENV = _get_env_from_input()
        _write_env_to_file(ENV)
    else:
        ENV = _get_env_from_file()
    return ENV


def _get_env_from_file():
    """Read KEY=VALUE in from the .env file"""
    ENV = {}
    if os.path.isfile(".env"):
        with open(".env", "r") as f:
            for line in f:
                key, value = line.rstrip("\n").split("=")
                ENV[key] = value
    return ENV


def _write_env_to_file(ENV):
    """ Write the variables to the .env file """
    with open(".env", "w") as f:
        for k, v in ENV.iteritems():
            print >>f, "{0}={1}".format(k, v)


def _get_env_from_input():
    """ Propmt the user for new environment variables and returns a dictionary """
    ENV = {}
    ENV['DEBUG'] = 'true'  # initial in case server is run by foreman
    ENV['PRODUCTION'] = ''  # initial in case server is run by foreman
    ENV['STAGING'] = 'true'  # initial in case server is run by foreman
    for variable in ENVIRONMENT_VARIABLES:
        if variable not in ENV:
            ENV[variable] = raw_input(
                "{0}: ".format(variable.replace("_", " ").title())).rstrip("\n")
    return ENV
