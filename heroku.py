import re

from fabric.api import local, task
try:
    from projectconf import DJANGO_PROJECT, ENVIRONMENT_VARIABLES
except ImportError:
    DJANGO_PROJECT = None
    ENVIRONMENT_VARIABLES = []


@task
def collect_static():
    """Heroku: Collects Static on Heroku """
    app = _prompt_for("app")
    local(
        'heroku run "cd {0};python manage.py collectstatic --noinput" --app {1}'.format(DJANGO_PROJECT, app))


@task
def config():
    """Heroku: Shows remote config """
    app = _prompt_for("app")
    local('heroku config --app {0}'.format(app))


@task
def config_push():
    """Heroku: Pushes your local .env configuration to Heroku """
    app = _prompt_for("app")
    local('heroku config:push --app {0}'.format(app))


@task
def config_pull():
    """Heroku: Pulls your heroku configuration to your local .env file and prompts for overwrites """
    app = _prompt_for("app")
    local('heroku config:pull --overwrite --interactive --app {0}'.format(app))


@task
def copy_database():
    """Heroku: Takes a database.dump file accessible from the web, and restores it into your heroku database """
    app = _prompt_for("app")
    setup_plugins(prompt=False, app=app)
    location = raw_input("Where is the database dump file?: ").rstrip("\n")
    database = _prompt_for("database", extra=app)
    local(
        "heroku pgbackups:restore {0} '{1}' --confirm {2}".format(database, location, app))


@task
def deploy():
    """Heroku: Push to origin then deploy to heroku, puts in maintainence mode too """
    remote = _prompt_for("remote")
    app = _get_heroku_apps(remote)
    # Do the pushes
    local('heroku maintenance:on --app {0}'.format(app))
    branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
    local('git push {0} {1}:master'.format(remote, branch))
    local('heroku maintenance:off --app {0}'.format(app))


@task
def logs():
    """Heroku: Run the logs command """
    app = _prompt_for("app")
    # see if the user wants to tail
    tail_prompt = raw_input("Tail? (Y/N): ").rstrip("\n")
    if tail_prompt.lower() == "y":
        tail = "--tail"
    else:
        tail = ""
    local('heroku logs {0} --app {1}'.format(tail, app))


@task
def setup_plugins(prompt=True, app=None):
    """Heroku: Checks if the plugins are setup correctly, and if they aren't, installs the plugins that the fabfile requires """
    if prompt:
        app = _prompt_for("app")
    if not "heroku-config" in local('heroku plugins --app {0}'.format(app), capture=True):
        local('heroku plugins:install git://github.com/ddollar/heroku-config.git --app {0}'.format(app))

    if not "pgbackups" in local('heroku addons --app {0}'.format(app), capture=True):
        local('heroku addons:add pgbackups --app {0}'.format(app))
    local('heroku config:add BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git --app {0}'.format(app))


@task
def setup_remotes():
    """Heroku: Sets up the remotes in the format heroku-staging and heroku-production """
    project = raw_input("Project name? ").rstrip("\n")
    local('git remote add heroku-staging git@heroku.com:propel-{0}-staging.git'.format(project))
    local('git remote add heroku-production git@heroku.com:propel-{0}-production.git'.format(project))


@task
def shell():
    """Heroku: Attaches itself to a django shell """
    app = _prompt_for("app")
    local('heroku run "cd {0};python manage.py shell" --app {1}'.format(DJANGO_PROJECT, app))


@task
def validate():
    """Heroku: Validates django project on Heroku"""
    app = _prompt_for("app")
    local('heroku run "cd {0};python manage.py validate" --app {1}'.format(DJANGO_PROJECT, app))

@task
def get_database_dump():
    database = raw_input("Database name: ").rstrip("\n")
    ip = raw_input("IP of Remote: ").rstrip("\n")
    local('createdb -Upostgres {0}'.format(database))
    local('taps pull postgres://postgres@localhost/{0} http://user:pass@{1}:5000'.format(database, ip))
    local('pg_dump -Fc --no-acl --no-owner -h localhost -U postgres {0} > {0}.dump'.format(database))



# Private, not picked up by Fabric
def _prompt_for(option_name, extra=None):
    """ Prompt for which heroku app, retries if fails"""
    if option_name == "remote":
        options, mapping, option_strings = _remotes()
    elif option_name == "app":
        options, mapping, option_strings = _apps()
    elif option_name == "database":
        options, mapping, option_strings = _databases(extra)
    if not options:
        return None

    print option_strings
    while True:
        try:
            index = raw_input(
                "Work with which {0}? (Type a number) (Ctrl+C to cancel): ".format(option_name)).rstrip("\n")
            option = options[mapping[index]]
        except KeyError:
            print "Invalid Option, try again (Ctrl+C to cancel)"
            continue
        break
    return option


def _map_list_to_numbers(option):
    """Get a dictionary of strings mapping to indexes of the list."""
    enumerated_options = []
    index = 1
    indexMapping = {}
    for i, appname in enumerate(option):
        enumerated_options.append('{0:3d} - {1}'.format(index, appname))
        indexMapping[str(index)] = i
        index += 1
    return indexMapping, "\n".join(enumerated_options)

def _databases(extra):
    databases = _get_heroku_databases(app=extra)
    mapping, database_strings = _map_list_to_numbers(databases)
    return databases, mapping, database_strings

def _get_heroku_databases(app=None):
    if not app:
        return "DATABASE"
    ugly = local('heroku pg:info --app {0}'.format(app), capture=True)
    regex = re.compile("HEROKU_POSTGRESQL_[A-Z]+_URL")
    return regex.findall(ugly)


def _remotes():
    remotes = _get_heroku_remotes()
    mapping, remote_strings = _map_list_to_numbers(remotes)
    return remotes, mapping, remote_strings

def _get_heroku_remotes():
    """Get a list of all the heroku remotes"""
    git_remotes = local('git remote -v', capture=True).split("\n")
    remotes = [remote.split()
               for remote in git_remotes if remote.split()[-1] == "(fetch)"]
    heroku_remotes = []
    for remote in remotes:
        if 'heroku' in remote[0]:
            heroku_remotes.append(remote[0])
    return heroku_remotes


def _apps():
    apps = _get_heroku_apps()
    mapping, app_strings = _map_list_to_numbers(apps)
    return apps, mapping, app_strings

def _get_heroku_apps(get_remote=None):
    """Get a list of all the apps from the git remotes"""
    git_remotes = local('git remote -v', capture=True).split("\n")
    remotes = [remote.split()
               for remote in git_remotes if remote.split()[-1] == "(fetch)"]
    apps = []
    for remote in remotes:
        if 'heroku' in remote[0]:
            app = re.split(':|\.', remote[1])[-2]
            if remote[0] == get_remote:
                return app
            apps.append(app)
    return apps


