import os, sys

from fabric.api import env, run, cd
from fabric.decorators import hosts


DEFAULTS = {
    'home': '/home/fhuser/',
    'repo_name': 'formhub',
    }

DEPLOYMENTS = { # why are these here, in a publically-posted file??
    'dev': {
        'home': '/home/ubuntu/srv/',
        'host_string': 'ubuntu@23.21.82.214', # TODO: switch to dev.formhub.org
        'project': 'formhub-ec2',
        'key_filename': os.path.expanduser('~/.ssh/modilabs.pem'),
    },
    'prod': {
        'home': '/home/ubuntu/srv/',
        'host_string': 'ubuntu@formhub.org',
        'project': 'formhub-ec2',
        'key_filename': os.path.expanduser('~/.ssh/modilabs.pem'),
    },
}

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
    env.wsgi_config_file = os.path.join(env.project_directory, 'formhub', 'wsgi.py')
    env.pip_requirements_file = os.path.join(env.code_src, 'requirements.pip')


def deploy(deployment_name, branch='master'):
    setup_env(deployment_name)
    with cd(env.code_src):
        run("git fetch origin")
        run("git checkout origin/%s" % branch)
        run("git submodule init")
        run("git submodule update")
        run('find . -name "*.pyc" -exec rm -rf {} \;')
    # numpy pip install from requirments file fails
    run("sudo pip install numpy --upgrade")
    run("sudo pip install -r %s --upgrade" % env.pip_requirements_file)
    with cd(env.code_src):
        run("python manage.py syncdb --settings='formhub.preset.default_settings'")
        run("python manage.py migrate --settings='formhub.preset.default_settings'")
        run("python manage.py collectstatic --settings='formhub.preset.default_settings' --noinput")
    run("sudo /etc/init.d/celeryd restart")
    run("sudo /etc/init.d/celerybeat restart")
    run("sudo /etc/init.d/formhub-uwsgi restart")
    run("sudo /etc/init.d/nginx restart")
