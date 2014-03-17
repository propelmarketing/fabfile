from fabric.api import local, task


@task
def update():
    local('git submodule foreach git pull origin master')
