from fabric.api import run, settings, local
#from fabric.decorators import hosts
#from fabric.operations import local

#@hosts('localhost')
def setup():
    "Clones inner repository"
    
    repos = ["git@github.com:mvpdev/django-eav.git",]
    
    for repo in repos:
        local("git clone %s" % repo, capture=True)

    # Here are some comments on virtualenv, pip, and fabric, for right
    # now I'm going to kludge something together with a sym link
    #http://stackoverflow.com/questions/1180411/activate-a-virtualenv-via-fabric-as-deploy-user
    # "pip install -e git+git://github.com/mvpdev/django-eav.git#egg=django-eav"
    local("ln -s django-eav/eav eav", capture=True)

    local("cp custom_settings_example.py custom_settings.py", capture=True)


def git_pull_all():
    "Merges master from repository & django-eav."
    local('git pull origin master', capture=True)
    local('cd django-eav && git pull origin master', capture=True)
