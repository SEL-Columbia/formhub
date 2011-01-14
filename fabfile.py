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
    env.db_name = 'nmispilot'
    _setup_path()

@hosts('wsgi@staging.mvpafrica.org')
def deploy_staging():
    staging_env()
    deploy()
    restart_wsgi()

@hosts('wsgi@staging.mvpafrica.org')
def deploy_production():
    production_env()
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
    require('root', provided_by=('staging', 'production'))
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    
    install_pip_requirements()
    with cd(env.code_root):
        run("git pull origin %(branch_name)s" % env)

def install_pip_requirements():
    """ deleting django-eav from the virtualenv in order to force a new download and avoid a pip error. """
    with cd(env.code_root):
        run("rm -r /home/wsgi/virtualenvs/django_odk/src/django-eav")
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
