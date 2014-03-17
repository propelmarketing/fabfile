Fabric Scripts
==============
Collection of fabric scripts that can help Propel be better.


### In the project's root there needs to be a file called 'projectconf.py' with the following parameters:
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
* $ fab setup
    * This runs the setup scripts to get the django app working on your server.
* $ fab development
    * This runs the development server.
* $ fab staging
    * This runs the staging server.
* $ fab production 
    * This runs the production server.
* $ fab test
    * Runs the default tests. 
* $ copy_media
    * Copies local media to s3


#### Heroku Setup:
* $ fab deploy
    * This prompts for the heroku remote app you want to use, then it turns
      maintainence on for that branch,
* $ fab copy_database
    * This will prompt you where the X.dump file is located, then restore that
      to the database.
* $ fab setup_heroku_remotes
    * Setup the heroku remotes in the format "propel-PROJECT-production" and
      "propel-PROJECT-staging" and prompting you for the project name. If the
naming structure differs, please do this manually. 
