from .core import update
from .django import test, copy_media, development, staging, production, setup
from .heroku import logs, config, config_push, config_pull, collect_static, deploy, copy_database, setup_remotes, setup_plugins, shell, validate
from .responsive import *
