"""
Tyrel Souza <tsouza@propelmarketing.com>
"""
import sys, os

from fabric.api import local, lcd
from fabric import context_managers

try:
    from projectconf import DJANGO_PROJECT, ENVIRONMENT_VARIABLES
except:
    DJANGO_PROJECT = None
    ENVIRONMENT_VARIABLES = []

def test():
    """Django: Runs the default tests"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with context_managers.shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py test')

def copy_media():
    """Django: Copies local media to s3"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = ''
    ENV['STAGING'] = 'True'
    with context_managers.shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py sync_media_s3 -p media')

def development():
    """Django: Run Server in Dev Mode"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'True'
    ENV['PRODUCTION'] = 'False'
    ENV['STAGING'] = 'True'
    with context_managers.shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')

def staging():
    """Django: Run server in Staging Mode"""
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'False'
    ENV['PRODUCTION'] = 'False'
    ENV['STAGING'] = 'True'
    with context_managers.shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')

def production():
    """Django: Run server in production mode """
    ENV = _get_env_from_file()
    ENV['DEBUG'] = 'False'
    ENV['PRODUCTION'] = 'True'
    ENV['STAGING'] = 'False'
    with context_managers.shell_env(**ENV):
        with lcd(_get_run_directory()):
            local('python manage.py runserver')

def setup():
    """Django: Setup Environment Variables, then pip install, then syncdb, finally migrate """
    ENV = _do_env_setup()
    cwd = _get_run_directory()

    # Run bash scripts
    if 'scripts' in os.listdir('.') and "setup.sh" in os.listdir('scripts'):
        local('./scripts/setup.sh')
    if 'scripts' in os.listdir('.') and "setup_dev.sh" in os.listdir('scripts'):
        local('./scripts/setup_dev.sh')

    local('pip install -r requirements.txt --allow-all-external')

    with context_managers.shell_env(**ENV):
        with lcd(cwd):
            _local_settings()
            local('python manage.py syncdb --noinput')
            local('python manage.py migrate')
            if DJANGO_PROJECT == "intake_forms":
                local('python manage.py load_fields')


# Private, not picked up by Fabric
def _get_run_directory():
    if not 'manage.py' in os.listdir('.'):
        cwd = DJANGO_PROJECT
    else:
        cwd = '.'
    return cwd
def _local_settings():
    """
        Copies local_settings.py.default to local_settings.py if needed
        WILL NOT OVERRIDE
    """
    files = os.listdir('.')
    if "local_settings.py.default" in files and  "local_settings.py" not in files:
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
    with open(".env", "r") as f:
        for line in f:
            key, value = line.rstrip("\n").split("=")
            ENV[key] = value
    return ENV

def _write_env_to_file(ENV):
    """ Write the variables to the .env file """
    with open(".env", "w") as f:
        for k,v in ENV.iteritems():
            print >>f, "{0}={1}".format(k,v)

def _get_env_from_input():
    """ Propmt the user for new environment variables and returns a dictionary """
    ENV = {}
    ENV['DEBUG'] = 'true' # initial in case server is run by foreman
    ENV['PRODUCTION'] = '' # initial in case server is run by foreman
    ENV['STAGING'] = 'true' # initial in case server is run by foreman
    for variable in ENVIRONMENT_VARIABLES:
        if variable not in ENV:
            ENV[variable] = raw_input("{0}: ".format(variable.replace("_", " ").title())).rstrip("\n")
    return ENV

