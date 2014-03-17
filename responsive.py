# TODO: 
#    1. All functions that require certain variable should check if vars are available
#       (currently only deploy checks it before aborting)
#    2. Adding a way to deploy a fresh project on host

# Dependencies:
#  1. Folder conventions (/var/www/vhosts/{app}.propelmarketing.com/....
#  2. Virtualenv
#  3. 'Supervisor' to make gunicorn into a service (will need a script for supervisor to
#       execute gunicorn.

import os
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from contextlib import contextmanager as _contextmanager
from time import sleep

# Globals 
# Custom variables
env.hosts = ['responsive.propelmarketing.com']
env.vhosts_dir = '/var/www/vhosts/responsive.propelmarketing.com'
env.app_name = 'responsive' # example: 'sprint'
env.app_template_name = 'responsive_templates'
env.remote_app_dir = "{0}/django/{1}".format(env.vhosts_dir, env.app_name)

# Template Fixtures Related
env.template_fixture_filename = 'templates.yaml'
env.remote_templates_dir = "{0}/django/{1}".format(env.vhosts_dir, env.app_template_name)
env.local_templates_dir = '../responsive_templates'
env.local_template_fixture = "{0}/{1}".format(env.local_templates_dir, env.template_fixture_filename)
env.remote_template_fixture = "{0}/{1}".format(env.remote_templates_dir, env.template_fixture_filename)

# Virtualenv
env.activate = 'source ' + env.vhosts_dir + '/virtualenv/bin/activate'


def _check_vars():
    # if all needed variables for deployment is not defined, stop right there
    if not env.hosts or not env.remote_app_dir or not env.app_name:
        print "Please set up the variables in the fab config file."
        return False

    return True


# Used for anything requiring virtualenv
@_contextmanager
def virtualenv():
    with cd(env.remote_app_dir):
        with prefix(env.activate):
            yield


##
## Main deployment function
##
def deploy():
    # make sure all variables are all set and make understandable aliases
    if not _check_vars():
        abort('Deploy process cannot be continued.')

    # Local
    # test()  # removed for now
    # push()

    # Remote
    update_code()
    update_dependencies()
    _copy_media()
    collectstatic()
    load_template()
    remote_migrate()
    stop_gunicorn()

    # Sometimes gunicorn would not start if I don't give it enough time
    print "Sleeping... Making sure the old processes are killed before starting new ones..."
    sleep(5)
    start_gunicorn()

# Atomic Functions
def help():
    print """
        # LOCAL
        help - Prints this message
        setup_localdev - Setup local development databases and media files
        deploy - Deploy to remote hosts through logical steps
        dump_template - Dump only template data and create 'fixtures/templates.yaml'
        test - Run unit and fts tests locally on specified app
        test_unit - Run all unit tests
        test_fts - Run all functional tests (dependent of port 8081)
        push - Push local repository to main repository
        copy_media_files - Copy media files from fixtures to root


        # REMOTE
        update_code - Pull and Update on remote hosts
        update_dependencies - Install any new dependencies in requirements.txt
        collectstatic - copy static files to STATIC_ROOT directory
        start_gunicorn - start gunicorn server
        stop_gunicorn - stop gunicorn server
        remote_migrate - migrate database on remote hosts
        """

def test():
    print "Running tests locally...."
    with settings(warn_only=True):
        result1 = test_unit()
        result2 = test_fts()
    if result1.failed or result2.failed and not confirm('Test failed.  Continue anyway?'):
        abort('Aborting at user request.')

def test_unit():
    print "Running Unit Tests"
    return local('sudo ./manage.py test %s.tests.unit' % env.app_name, capture=False)
    
def test_fts():
    print "Running Integration Tests"
    local('cp -r ./fixtures/media ./')  # old assets need for test template
    return local('sudo ./manage.py test %s.tests.fts --liveserver localhost:8081' % env.app_name, capture=False)

def push():
    print "Pushing local repository to main repository..."
    with settings(warn_only=True):
        local('hg push', capture=False)

def update_code():
    if run("test -d %s" % env.remote_app_dir).failed:
        print "Remote App Directory does not exist"
        ## NEED IMPROVEMENT
        raise
    with cd(env.remote_app_dir):
        run('hg pull')  # pull remotely
        run('hg up')

# Update any new dependencies
def update_dependencies():
    if run("test -f %s/requirements.txt" % env.remote_app_dir).succeeded:
        with virtualenv():
            run("pip install -r requirements.txt")

def remote_migrate():
    with cd(env.remote_app_dir):
        with virtualenv():
            run('./manage.py migrate')

def _copy_media():
    with cd(env.remote_app_dir):
        sudo("cp -r {0}/template_assets ./media".format(env.remote_templates_dir))

def collectstatic():
    with cd(env.remote_app_dir):
        with virtualenv():
            run('./manage.py collectstatic --noinput')

def load_template():
    with cd(env.remote_app_dir):
        with virtualenv():
            run('./manage.py loaddata {0}'.format(env.remote_template_fixture))

def stop_gunicorn():
    print "Stopping gunicorn servers using Supervisor"
    sudo('supervisorctl stop {0}'.format(env.app_name))

def start_gunicorn():
    print "Starting gunicorn servers using Supervisor"
    sudo('supervisorctl start {0}'.format(env.app_name))

## Copied from the original development fabfile
def deploy_localdev():
    # Prepare a local_settings.py if one isn't present
    local_settings_replacements = [
        ("'ENGINE': 'django.db.backends.'", "'ENGINE': 'django.db.backends.sqlite3'"),
        ("'NAME': ''", "'NAME': '../resources/dev.db'"),
        ("DEBUG = False", "DEBUG = True")
    ]
    if os.path.isfile("./local_settings.py"):
        local("rm ./local_settings.py")
    local("cp ./local_settings.py.default ./local_settings.py")
    local_settings = open("./local_settings.py").read()
    for search, replace in local_settings_replacements:
        local_settings = local_settings.replace(search, replace)
    open("./local_settings.py", "w").write(local_settings)


    # Test first to make sure we're okay to proceed
    #local("./manage.py test responsive")

    setup_localdev()

    # Install requirements
    # local("pip install -r requirements.txt")

def _reset_dev_dbs():
    ### remove the dev database file if it exists
    if os.path.isfile("../resources/dev.db"):
        local("rm ../resources/dev.db")
    elif os.path.isfile("dev.db"):
        local("rm dev.db")

    ### Sync the DB
    local("./manage.py syncdb --noinput")
    local("./manage.py migrate")

    ### Remove all content_types data to load custom fixtures
    #  (this step can be bypassed by dumpdata with --natural flag and removing the contenttypes &
    #    permissions data from the fixture)
    # local("./manage.py reset contenttypes --noinput") 

def _load_dev_fixtures():
    ### Load the Dev fixtures
    local("./manage.py loaddata fixtures/dev.yaml")
    _load_local_templates_fixtures()

def _load_test_fixtures():
    ### Load the Test fixtures
    local("./manage.py loaddata fixtures/test.yaml")
    _load_local_templates_fixtures()

def _load_local_templates_fixtures():
    local("./manage.py loaddata {0}".format(env.local_template_fixture))  # has all available templates of repository


def setup_localdev():
    _reset_dev_dbs()
    _load_dev_fixtures()
    copy_media_files()

def setup_localtestdev():
    _reset_dev_dbs()
    _load_test_fixtures()
    copy_media_files()

def copy_media_files():
    # Load media files
    local("cp -r {0}/template_assets ./media".format(env.local_templates_dir))

def update_test_template():
    test_fixture = 'fixtures/test.yaml'
    with settings(warn_only=True):
        if local("test -f %s" % test_fixture).succeeded:
            print "### Backing up old {0} to {0}.bak ### ".format(test_fixture)
            local("mv {0} {0}.bak".format(test_fixture))
    print ("### Dumping new {0} from database ### ".format(test_fixture))
    local("./manage.py dumpdata --format=yaml --indent=4 --natural\
            responsive auth.user admin sites agency > {0}".format(test_fixture))

def update_dev_template():
    dev_fixture = 'fixtures/dev.yaml'
    with settings(warn_only=True):
        if local("test -f %s" % dev_fixture).succeeded:
            print "### Backing up old {0} to {0}.bak ### ".format(dev_fixture)
            local("mv {0} {0}.bak".format(dev_fixture))
    print ("### Dumping new {0} from database ### ".format(dev_fixture))
    local("./manage.py dumpdata --format=yaml --indent=4 --natural\
            --exclude=responsive.Template \
            --exclude=responsive.TemplateVersion \
            --exclude=responsive.TemplateSettingsField \
            --exclude=responsive.TemplateSettingsFile \
            --exclude=responsive.TemplateAsset \
            --exclude=responsive.FieldGroup \
            responsive auth.user admin sites agency \
            > {0}".format(dev_fixture))
    

# This method helps designers to dump template data and update to repository
def dump_template():
    with settings(warn_only=True):
        if local("test -f %s" % env.local_template_fixture).succeeded:
            print "### Backing up old {0} to {0}.bak ### ".format(env.local_template_fixture)
            local("mv {0} {0}.bak".format(env.local_template_fixture))
    print ("### Dumping new template.yaml from database ### ")
    local("./manage.py dumpdata --format=yaml --indent=4 \
            responsive.Template \
            responsive.TemplateVersion \
            responsive.TemplateSettingsField \
            responsive.TemplateSettingsFile \
            responsive.TemplateAsset \
            responsive.FieldGroup \
            > {0}".format(env.local_template_fixture))
