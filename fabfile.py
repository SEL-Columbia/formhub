from fabric.api import run, settings, local
#from fabric.decorators import hosts
#from fabric.operations import local

#@hosts('localhost')
def git_clone():
    "Clones the repositories"
    
    odk_repo = "git@github.com:mvpdev/odk_dropbox.git"
    nmis_analysis_repo = "git@github.com:mvpdev/nmis_analysis.git"
    django_eav_repo = "git@github.com:mvpdev/django-eav.git"
    
    local('git clone %s odk_dropbox' % odk_repo, capture=True)
    local("git clone %s nmis_analysis" % nmis_analysis_repo, capture=True)
    local("git clone %s django_eav" % django_eav_repo, capture=True)

def git_pull_all():
    "Updates all the repositories"
    
    local('cd odk_dropbox && git pull origin master', capture=True)
    local('cd nmis_analysis && git pull origin master', capture=True)
    local('cd django_eav && git pull origin master', capture=True)
