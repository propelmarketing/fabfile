Fabric Scripts
==============
Collection of fabric scripts that can help Propel be better. Written by
Tyrel Souza <tsouza@propelmarketing.com>


### Setup
* Make sure Fabric 1.8.2 or better is installed
* To Include in codebase

```bash
  $ git submodule add git@github.com:propelmarketing/fabfile.git fabfile
  $ git submodule init
  $ git submodule update
```

* To update

```bash
 $ fab core.update
```

### In the project's root there needs to be a file called 'projectconf.py' (projectconf.py.sample provided) with the following parameters:
* ENVIRONMENT_VARIABLES A list of Environment variables to configure
* DJANGO_PROJECT The name of the django project module

Example:

```python
    DJANGO_PROJECT = 'fabtastic'
    ENVIRONMENT_VARIABLES = ['DEBUG','PRODUCTION','DATABASE_NAME']
```

The reasoning for this to be hardcoded is that it's a catch 22 to read from the
django settings, you need to know the project name to access settings, so you can't store it in the django settings. (If anyone knows a better way to do this, please create a pull request!)

#### Core scripts:
* $ fab update 
    * Updates the fabfile submodule.

#### Django Setup:
* $ fab dj.setup
    * This runs the setup scripts to get the django app working on your server.
* $ fab dj.development
    * This runs the development server.
* $ fab dj.staging
    * This runs the staging server.
* $ fab dj.production 
    * This runs the production server.
* $ fab dj.test
    * Runs the default tests. 
* $ fab dj.copy_media
    * Copies local media to s3
* $ fab dj.shell
    * Runs a Django Shell
* $ fab dj.superuser
    * Create a Superuser with prompts


#### Heroku Setup:
* $ fab heroku.deploy
    * This prompts for the heroku remote app you want to use, then it turns
      maintainence on for that branch,
* $ fab heroku.copy_database
    * This will prompt you where the X.dump file is located, then restore that
      to the database.
* $ fab heroku.setup_remotes
    * Setup the heroku remotes in the format "propel-PROJECT-production" and
      "propel-PROJECT-staging" and prompting you for the project name. If the
naming structure differs, please do this manually. 
* $ fab heroku.logs
    * Show Heroku logs, prompts for tail or not.
* $ fab heroku.config
    * Show heroku config
* $ fab heroku.config_push
    * Pushes local .env file to Heroku
* $ fab heroku.config_pull
    * Pulls Heroku env into local .env file
* $ fab heroku.collect_static
    * Runs collect static on heroku
* $ fab heroku.setup_plugins
    * Sets up the all the plugins and addons that we require to run a site on heroku.o
* $ fab heroku.shell
    * Attaches to a heroku django shell.
* $ fab heroku.validate
    * Validates the django code on heroku







### Contributing
If you contribute any code to the fabfile repository, please remember to update
__init__.py with the function you added (or removed). Thank you.
