import os
from fabric.api import env, cd, run
from datetime import datetime

# default settings for all deployments
env.update(
    {
        'deployments_path': '/home/wsgi/srv',
        'project_name': 'nmis',
        'virtualenv_directory': 'project_env',
        'migrate': True,
        }
    )

DEPLOYMENTS = {
    'dev': {
        'folder_name': 'nmis_dev',
        'host_string': 'wsgi@staging.mvpafrica.org',
        'branch': 'feature/dj13',
        'backup': False,
        },
    'staging': {
        'folder_name': 'nmis_dev',
        'host_string': 'wsgi@nmis-dev.mdgs.gov.ng',
        'branch': 'feature/dj13',
        'backup': False,
        },
    'production': {
        'folder_name': 'nmis_production',
        'host_string': 'wsgi@nmis-dev.mdgs.gov.ng',
        'branch': 'feature/dj13',
        'backup': True,
        'database_name': 'nmis_production',
        }
    }


def _setup_env(deployment_name):
    env.update(DEPLOYMENTS[deployment_name])
    env.project_path = os.path.join(
        env.deployments_path,
        env.folder_name
        )
    env.code_path = os.path.join(
        env.project_path,
        'nmis'
        )
    env.apache_dir = os.path.join(
        env.project_path,
        'apache'
        )


def backup(deployment_name):
    _setup_env(deployment_name)
    cur_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    env.backup_directory_path = os.path.join(
        env.project_path,
        'backups',
        cur_timestamp
        )
    run("mkdir -p %(backup_directory_path)s" % env)
    with cd(env.backup_directory_path):
        run("mysqldump -u root -p %(database_name)s > %(database_name)s.sql" % env)
        run("gzip %(database_name)s.sql" % env)


def deploy(deployment_name, reload="none"):
    """
    Example command line usage:
    fab deploy:staging,reparse=none
    """
    _setup_env(deployment_name)
#    import json
#    print json.dumps(env)
#    import sys
#    sys.exit(0)

    if env.backup:
        backup(deployment_name)
    
    def pull_code():
        """
        Pull updated code from nmis repo.
        """
        with cd(env.code_path):
            run("git pull origin %(branch)s" % env)
    pull_code()
    
    def pull_data():
        with cd(os.path.join(env.code_path, 'data')):
            run("git pull origin master")
    pull_data()

    def _run_in_virtualenv(command):
        activate_path = os.path.join(
            env.project_path,
            env.virtualenv_directory,
            'bin', 'activate'
            )
        activate_virtualenv = "source %s" % activate_path
        run(activate_virtualenv + ' && ' + command)

    def install_pip_requirements():
        with cd(env.code_path):
            _run_in_virtualenv("pip install -r requirements.pip")
    install_pip_requirements()

    # NOTE: I recently installed the registration app, to get this
    # working you need to use a syncdb, migrate isn't enough.
    def migrate_database():
        if env.migrate:
            with cd(env.code_path):
                _run_in_virtualenv("python manage.py migrate")

    def reload_fixtures(flag=""):
        with cd(env.code_path):
            _run_in_virtualenv("python manage.py load_fixtures %s" % flag)

    if reload == "all":
        print "Loading all data in from csvs."
        reload_fixtures("-S")
    elif reload == "limit":
        reload_fixtures("--limit")
    elif reload == "table_defs":
        reload_fixtures("load_table_defs")

    def collect_static():
        with cd(env.code_path):
            _run_in_virtualenv("python manage.py collectstatic --noinput")
    collect_static()
    
#    migrate_database()
#    def reparse_surveys():
#        with cd(env.code_path):
#            _run_in_virtualenv("python manage.py reparse")
#    if reparse == "all":
#        reparse_surveys()

    def restart_web_server():
        """
        touch wsgi file to trigger reload
        """
        with cd(env.apache_dir):
            run("touch environment.wsgi")
    restart_web_server()
