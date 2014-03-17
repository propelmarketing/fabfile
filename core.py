from fabric.api import local


def update():
    local('git submodule foreach git pull origin master')
