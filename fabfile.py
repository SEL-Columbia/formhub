import os, sys

from fabric.api import env, run, cd
from fabric.decorators import hosts


DEFAULTS = {
    'home': '/home/wsgi/srv/',
    'repo_name': 'formhub',
    }

DEPLOYMENTS = {
    'alpha': {
        'host_string': 'wsgi@nmis-linode.mvpafrica.org',
        'project': 'ei_surveyor_alpha',
        'branch': 'master',
    },
    'dev': {
        'host_string': 'wsgi@nmis-linode.mvpafrica.org',
        'project': 'formhub_dev',
        'branch': 'master',
    },
    # 'prod': {
    #     'project': 'xls2xform_production',
    #     'branch': 'master',
    # }
    'ec2': {
        'home': '/home/ubuntu/srv/',
        'host_string': 'ubuntu@23.21.134.243',
        'project': 'formhub-ec2',
        'branch': 'master',
        'key_filename': os.path.expanduser('~/.ssh/modilabs.pem'),
    },
}


def run_in_virtualenv(command):
    d = {
        'activate': os.path.join(
            env.project_directory, 'project_env', 'bin', 'activate'),
        'command': command,
        }
    run('source %(activate)s && %(command)s' % d)


def check_key_filename(deployment_name):
    if DEPLOYMENTS[deployment_name].has_key('key_filename') and \
        not os.path.exists(DEPLOYMENTS[deployment_name]['key_filename']):
        print "Cannot find required permissions file: %s" % \
            DEPLOYMENTS[deployment_name]['key_filename']
        return False
    return True

def setup_env(deployment_name):
    env.update(DEFAULTS)
    env.update(DEPLOYMENTS[deployment_name])
    if not check_key_filename(deployment_name): sys.exit(1)
    env.project_directory = os.path.join(env.home, env.project)
    env.code_src = os.path.join(env.project_directory, env.repo_name)
    env.wsgi_config_file = os.path.join(
        env.project_directory, 'apache', 'environment.wsgi')
    env.pip_requirements_file = os.path.join(env.code_src, 'requirements.pip')


def deploy(deployment_name):
    setup_env(deployment_name)
    with cd(env.code_src):
        run("git pull origin %(branch)s" % env)
        run('find . -name "*.pyc" -exec rm -rf {} \;')
    run_in_virtualenv("pip install -r %s" % env.pip_requirements_file)
    with cd(env.code_src):
        run_in_virtualenv("python manage.py migrate")
        run_in_virtualenv("python manage.py collectstatic --noinput")
    run('touch %s' % env.wsgi_config_file)
