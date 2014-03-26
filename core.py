from fabric.api import local, task


@task
def update():
    """Core: Update the submodules to point to newest master"""
    local('git submodule foreach git pull origin master')
