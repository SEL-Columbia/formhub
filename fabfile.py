import os

from fabric.api import *
from fabric.contrib import files, console
from fabric import utils
from fabric.decorators import hosts

from datetime import datetime

env.home = '/home/wsgi/'
env.project = 'nmis'

# modified this script from caktus 
# https://bitbucket.org/copelco/caktus-deployment/src/tip/example-django-project/caktus_website/fabfile.py#cl-144

def _setup_path():
    env.root = os.path.join(env.home, 'srv', env.code_directory)
    env.code_root = os.path.join(env.root, env.project)
    env.apache_dir = os.path.join(env.root, "apache")
    env.settings = '%(project)s.settings' % env
    env.backup_dir = os.path.join(env.root, "backups")
    env.run_migration = False

def staging_env():
    """ use staging environment on remote host"""
    env.code_directory = 'nmis-staging'
    env.environment = 'staging'
    env.branch_name = 'develop'
    _setup_path()

def production_env():
    """ use production environment on remote host"""
    env.code_directory = 'nmis-production'
    env.environment = 'production'
    env.branch_name = 'master'
    env.db_name = 'nmispilot_phaseII'
    _setup_path()

@hosts('wsgi@staging.mvpafrica.org')
def deploy_staging(migrate_db='no'):
    staging_env()
    if migrate_db == 'migrate': env.run_migration = True
    deploy()
    restart_wsgi()

@hosts('wsgi@staging.mvpafrica.org')
def deploy_production(migrate_db='no'):
    production_env()
    if migrate_db == 'migrate': env.run_migration = True
    deploy()
    restart_wsgi()

@hosts('wsgi@staging.mvpafrica.org')
def backup_production():
    production_env()
    backup_code_and_database()

def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=('staging', 'production'))

def backup_code_and_database():
    cur_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_directory_path = os.path.join(env.backup_dir, cur_timestamp)
    tarball_path = os.path.join(backup_directory_path, env.project)
    run("mkdir -p %s" % backup_directory_path)

    with cd(env.root):
        run("tar -cvf %s.tar %s" % (tarball_path, env.project))

    with cd(backup_directory_path):
        run("mysqldump -u nmis -p$MYSQL_NMIS_PW %(db_name)s > %(db_name)s.sql" % env)

def deploy():
    """ git pull (branch) """
    #will pull the same branch as for the main repo
    sub_repositories = ["xform_manager"]
    sub_repo_paths = [os.path.join(env.code_root, repo) for repo in sub_repositories]
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production? (Always back up-- "fab backup_production")',
                               default=False):
            utils.abort('Production deployment aborted.')
    with cd(env.code_root):
        run("git pull origin %(branch_name)s" % env)
    
    for repo_path in sub_repo_paths:
        with cd(repo_path):
            run("git pull origin %(branch_name)s" % env)
    
    if env.run_migration:
        with cd(env.code_root):
            run("python manage.py migrate")
    
    install_pip_requirements()

def install_pip_requirements():
    """ deleting django-eav from the virtualenv in order to force a new download and avoid a pip error. """
    with cd(env.code_root):
        run("pip install -r requirements.txt")

def restart_wsgi():
    """ touch wsgi file to trigger reload """
    with cd(env.apache_dir):
        run("touch environment.wsgi")

def apache_restart():
    """ restart Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    run('sudo apache2ctl restart')

# I need to import all the phase one data
# find /home/amarder/host/Desktop/Phone\ Data\ Phase\ I/ -name "???" -exec python manage.py import_instances '{}' \;

#the following method uses fab as an alternative to a shell script, which is
#not a clean use of fab
def local_ensure_git_subrepositories_loaded():
    repositories_to_ensure = {
        'xform_manager': 'git://github.com/mvpdev/xform_manager.git'
    }
    current_dir = os.path.dirname(__file__)
    for repo_name, repo_link in repositories_to_ensure.items():
        if not os.path.exists(os.path.join(current_dir, repo_name)):
            local('git clone %s' % repo_link)
