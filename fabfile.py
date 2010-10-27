from fabric.api import run, settings

def git_clone():
    "Clones the repositories"
    
    odk_repo = "git@github.com:mvpdev/odk_dropbox.git"
    nmis_analysis_repo = "git@github.com:mvpdev/nmis_analysis.git"
    django_eav_repo = "git@github.com:mvpdev/django-eav.git"
    
    run("git clone %s odk_dropbox" % odk_repo)
    run("git clone %s nmis_analysis" % nmis_analysis_repo)
    run("git clone %s django_eav" % django_eav_repo)

def git_pull():
    "Updates all the repositories"
    
    with('cd odk_dropbox'):
        run('git pull origin master')
    
    with('cd nmis_analysis'):
        run('git pull origin master')
    
    with('cd django_eav'):
        run('git pull origin master')
