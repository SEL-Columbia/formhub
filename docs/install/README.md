# Installation Guide

*This document describes how to install formhub from source, and run it as a dedicated server image. If you wish to run it on a shared computer, the use of a virtualized environment, such as [VirtualBox](https://www.virtualbox.org/) is recommended. Using either [debian](http://www.debian.org/) or [ubuntu](http://www.ubuntu.com/) for the operating system (OS) is recommended. If you choose a different server OS, you will need to replace the [apt-get](https://help.ubuntu.com/community/AptGet/Howto) command with the one corresponding to your system's package manager.*

*As an alternative to installing from source, you can just use these pre-built server images instead:*

* The public Formhub Amazon Machine Image (AMI) to [Run Your Own Formhub Instances on Amazon Web Services (AWS)](https://github.com/SEL-Columbia/formhub/wiki/How-To-Run-Your-Own-Formhub-Instances-on-Amazon-Web-Services)

* The public Formhub Virtual Disk Image (VDI) to [Run Your Own Formhub Instances on VirtualBox](https://github.com/SEL-Columbia/formhub/wiki/How-To-Run-Your-Own-Formhub-Virtual-Machines-on-VirtualBox)

## *Required Steps*

## 1. Basic System Libraries and Packages

Install using a terminal or command line prompt as the [root](https://wiki.debian.org/Root) user in debian or with the [sudo](https://help.ubuntu.com/community/RootSudo) command in ubuntu:

```
$ sudo apt-get update; sudo apt-get upgrade -y
$ sudo apt-get install -y git build-essential python-all-dev \
  python-pip python-lxml python-magic python-imaging default-jre \
  libjpeg-dev libfreetype6-dev zlib1g-dev rabbitmq-server libxslt1-dev
```

## 2. Define the formhub user account 

Create <tt>fhuser</tt>, the user account which will own and run the formhub processes, and set its password:

```
$ sudo adduser fhuser
$ sudo passwd fhuser
```

## 3. Install [mongoDB](http://mongodb.org/)

According to the mongoDB installation instructions for [debian](http://docs.mongodb.org/manual/tutorial/install-mongodb-on-debian/) and [ubuntu](http://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/).

Import the public key:

```
$ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
```

Next, for debian:

```
$ echo 'deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
```

Or ubuntu:
```
$ echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
```

Then finally for either system:
```
$ sudo apt-get update
$ sudo apt-get install mongodb-org 
```

## 4. Install [PostgreSQL](http://www.postgresql.org/)

*Prior versions of formhub used [MySQL](https://www.mysql.com/), and while it is technically possible to use it instead, PostgreSQL is strongly recommended.*

Install the required packages and libraries:

```
$ sudo apt-get install -y postgresql python-psycopg2 postgresql-contrib
$ sudo pip install south
```

Then configure the database for formhub. Create a data folder for the database to use:

```
$ sudo /etc/init.d/postgresql stop
$ sudo mkdir -p /opt/data/formhub/pgsql
$ cd /opt/data/formhub
$ sudo chown postgres pgsql
```

Next, update the configuration file to use it, saving the original version of the <tt>postgresql.conf</tt> in <tt>/etc/postgresql/9.1/main</tt> before making any edits:

```
$ cd /etc/postgresql/9.1/main
$ sudo cp -ip postgresql.conf postgresql.conf.org
```

Change the <tt>data_directory</tt> variable to point to the pgsql formhub data folder (i.e., <tt>/opt/data/formhub/pgsql</tt>).

Unless you already have a valid [SSL certificate](https://help.ubuntu.com/12.04/serverguide/certificates-and-security.html) installed, turn off the <tt>ssl</tt> option:

```
$ sudo vi postgresql.conf
# (edit lines 41 and 80 -- here is the before and after) 
$ diff postgresql.conf.org postgresql.conf
41c41
< data_directory = '/var/lib/postgresql/9.1/main'		# use data in another directory
---
> data_directory = '/opt/data/formhub/pgsql'
80c80
< ssl = true				# (change requires restart)
---
> ssl = false				# (change requires restart)
```
Switch to the <tt>postgres</tt> account and initialize the database and database user for access by the formhub [django](https://www.djangoproject.com/) application.

```
$ sudo su - postgres 
$ /usr/lib/postgresql/9.1/bin/initdb -D /opt/data/formhub/pgsql
$ /usr/lib/postgresql/9.1/bin/pg_ctl -D /opt/data/formhub/pgsql -l logfile start
$ /usr/lib/postgresql/9.1/bin/createuser -P formhubDjangoApp
```

Enter a password for the <tt>formhubDjangoApp</tt> database user. You will need this later, for the in the django <tt>default_settings.py</tt> file.

Say no (<tt>n</tt>) to the next series of permission questions:

```
Shall the new role be a superuser? (y/n) n
Shall the new role be allowed to create databases? (y/n) n
Shall the new role be allowed to create more new roles? (y/n) n
```

Create the logical database <tt>FormhubDjangoDB</tt> for the formhub django application and enable uuid creation:

```
$ /usr/lib/postgresql/9.1/bin/createdb FormhubDjangoDB
$ /usr/lib/postgresql/9.1/bin/psql -d FormhubDjangoDB
```

You will be presented with the <tt>FormhubDjangoDB=#</tt> prompt. Enter the following command, then <tt>\q</tt> to exit the database shell:

```
FormhubDjangoDB=# CREATE EXTENSION "uuid-ossp";
FormhubDjangoDB=# \q
```

Finally, turn postgres off, and exit the postgres account:

```
$ /usr/lib/postgresql/9.1/bin/pg_ctl -D /opt/data/formhub/pgsql -l logfile stop
$ exit
```
Continue as the root or sudo user to edit the <tt>pg_hba.conf</tt> file for database access security.

As always, copy the existing configuration file first, before making any edits, then change line 90 from <tt>peer</tt> to <tt>md5</tt> (for more about these options, see the [pg_hba.conf](http://www.postgresql.org/docs/9.3/static/auth-pg-hba-conf.html) file documentation): 

```
$ cd /etc/postgresql/9.1/main
$ sudo cp -ip pg_hba.conf pg_hba.conf.org
$ sudo vi pg_hba.conf
# (here is the before and after)
$ diff pg_hba.conf.org pg_hba.conf
90c90
< local   all             all                                     peer
---
> local   all             all                                     md5
```

Restart the database, and test that it asks for a password for access:

```
$ sudo /etc/init.d/postgresql restart
$ /usr/lib/postgresql/9.1/bin/psql -d FormhubDjangoDB -U formhubDjangoApp -h localhost
```

If your configurations are correct, you should be prompted for a password, like this:

```
Password for user formhubDjangoApp: 
```

You can either input the password you used to create the <tt>formhubDjangoApp</tt> user earlier, then type <tt>\q</tt> to exit, or just <tt>Control-C</tt> to quit.

*Phew!* 

That was a lot of work, but your databases are ready, and you won't have to touch these settings again, even if you have to reboot or restart the server later.

## 5. Install formhub 

Switch to the <tt>fhuser</tt> account and make sure you are in the home folder of the correct account:

```
$ sudo su - fhuser
$ pwd
$ whoami
```

You should see <tt>/home/fhuser</tt> as the result of the <tt>pwd</tt> command, and <tt>fhuser</tt> as the result of <tt>whoami</tt>. 

Obtain the [formhub source](https://github.com/SEL-Columbia/formhub.git) from [github](https://github.com/):

```
$ git clone https://github.com/SEL-Columbia/formhub.git
```

*If you are using this guide before this branch (<tt>slim_dedicated_server</tt>) has been merged into the formhub master branch, then you will need to use [git's checkout](http://csurs.csr.uky.edu/cgi-bin/man/man2html?1+git-checkout) command first, as follows:*

```
$ cd ~/formhub
$ git checkout slim_dedicated_server
```

*Then confirm you are on the correct branch, before continuing:*

```
$ git branch
```

*You should see <tt>slim_dedicated_server</tt> marked with an asterisk, like this:*

```
  master
* slim_dedicated_server
```

As root or sudo, install the python packages required for formhub:

```
$ sudo pip install -r /home/fhuser/formhub/requirements.pip
```

Next, edit the <tt>default_settings.py</tt> file in <tt>/home/fhuser/formhub/formhub/preset</tt> (you can use [vim](https://wiki.debian.org/vim), [nano](http://www.nano-editor.org/dist/v1.2/faq.html), or any other [text editor](https://wiki.debian.org/TextEditor)) and change the database user password in line 21 from <tt>foo</tt> to the password you created earlier for the <tt>formhubDjangoApp</tt> user:

```
DATABASES['default']['PASSWORD'] = 'foo' # put your password here
```

Then set the required environment variables for formhub by adding these two lines to the end of the <tt>/home/fhuser/.profile</tt> file:

```
export PYTHONPATH=$PYTHONPATH:/home/fhuser/formhub/formhub
export DJANGO_SETTINGS_MODULE=formhub.preset.default_settings
```

Apply the changes to the environment by sourcing the updated file:

```
$ source ~/.profile
```

To confirm the environment settings are correct, run django's [validate](https://docs.djangoproject.com/en/1.5/ref/django-admin/#validate) command from inside the formhub folder:

```
$ cd ~/formhub
$ python manage.py validate
```

If everything is ok, you should see this:

```
Your environment is:"formhub.preset.default_settings"
0 errors found
```

Now you are ready to install the formhub data models into the database:

```
$ cd ~/formhub
$ python manage.py syncdb --noinput
$ python manage.py migrate
```

## 6. Install [celery](http://celeryproject.org/) as a daemon

Copy the celery scripts into <tt>/etc/init.d</tt> and <tt>/etc/default</tt> as the root user in debian or with the sudo command in ubuntu, and set their run permissions accordingly:

```
$ sudo cp -ip /home/fhuser/formhub/extras/celeryd/etc/init.d/celeryd /etc/init.d/celeryd
$ sudo cp -ip /home/fhuser/formhub/extras/celeryd/etc/default/celeryd /etc/default/celeryd
$ sudo chmod 755 /etc/init.d/celeryd
```

Switch back to the <tt>fhuser</tt> account, and confirm that you can start celery as a daemon process:

```
$ /etc/init.d/celeryd start
```

If successful, you should see:

```
Your environment is:"formhub.preset.default_settings"
celeryd-multi v3.0.23 (Chiastic Slide)
> Starting nodes...
	> w1.: Your environment is:"formhub.preset.default_settings"
OK
```

Finally, use [insserv](https://wiki.debian.org/LSBInitScripts/DependencyBasedBoot) (or [upstart](http://upstart.ubuntu.com/cookbook/) in ubuntu, depending on your version) to have the celery daemon start automatically on boot:

```
sudo /sbin/insserv celeryd
```

## 7. Start the server

Now, you should be ready to bring up the server as user <tt>fhuser</tt> with django's [built-in web server](https://docs.djangoproject.com/en/1.5/ref/django-admin/#runserver-port-or-address-port): 

```
$ cd ~/formhub
$ python manage.py runserver
```

You should see this response from the terminal:

```
Your environment is:"formhub.preset.default_settings"
Validating models...

0 errors found
April 28, 2014 - 16:26:42
Django version 1.5.6, using settings 'formhub.preset.default_settings'
Development server is running at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Open a web browser and visit <tt>http://127.0.0.1:8000/</tt> while the server is running and you should see the formhub home page.

*Great success!*

If you are doing some small-scale experiments in your own environment, then you are done.

If, however, you wish to host your own instance of formhub on a public server, or on a public server with your own domain or subdomain (for example, <tt>http://formhub.example.org/</tt>), then you'll need to deploy django [with wsgi](https://docs.djangoproject.com/en/1.5/howto/deployment/wsgi/) behind a full webserver, as described in the optional steps, below.

## *Optional Steps*

## 8. Deploy Django with WSGI to run behind a full web server

While there are several [WSGI](http://www.wsgi.org/) applications available, using [uWSGI](http://projects.unbit.it/uwsgi/) is recommended. [Installation](http://uwsgi-docs.readthedocs.org/en/latest/Install.html) is simple:

```
$ sudo pip install uwsgi
```

Next, create the log folder and make it accessible for the <tt>fhuser</tt>:

```
$ sudo mkdir /var/log/uwsgi
$ sudo chmod 755 /var/log/uwsgi
$ sudo chown fhuser:fhuser /var/log/uwsgi
```

Install the <tt>formhub-uwsgi</tt> startup script so that uWSGI will start automatically on boot:

```
$ cd /etc/init.d
$ sudo cp -ip /home/fhuser/formhub/extras/formhub-uwsgi .
$ sudo /sbin/insserv formhub-uwsgi
$ sudo /etc/init.d/formhub-uwsgi start
```

Going forward, you can use <tt>/etc/init.d/formhub-uwsgi start|stop|restart</tt> to control uWSGI.

The uWSGI server writes to a log file named <tt>/var/log/uwsgi/formhub.log</tt> which you can read using  [head, tail, less](http://www.tldp.org/LDP/GNU-Linux-Tools-Summary/html/x6546.htm), etc.

This guide will use [nginx](http://nginx.org/) as the web server to use in conjection with uWSGI and Django.

Following the [ngnix installation instructions](http://nginx.org/en/linux_packages.html#stable), download the nginx signing key and update the package manager's source list.

This particular example is for Debian 7 (codename *wheezy*):

```
$ cd /opt
$ sudo mkdir -p downloads/nginx
$ cd downloads/nginx
$ sudo wget http://nginx.org/keys/nginx_signing.key
$ sudo apt-key add nginx_signing.key
$ cd /etc/apt
$ sudo cp -ip sources.list sources.list.org
$ sudo vi sources.list
$ diff sources.list.org sources.list
# (after editing the sources.list file)
15a16,19
> 
> # nginx
> deb http://nginx.org/packages/debian/ wheezy nginx
> deb-src http://nginx.org/packages/debian/ wheezy nginx
$ sudo apt-get update; apt-get install -y nginx
```

You should be able to see the nginx server running by visiting <tt>http://127.0.0.1</tt> in a web browser.

There should be a notice that says:

> Welcome to nginx!
> 
> If you see this page, the nginx web server is successfully installed and working. Further configuration is required.

Finally, configure nginx to send all the Django requests to the uWSGI server and confirm they are correct:

```
$ cd /etc/nginx/conf.d
$ sudo mv default.conf default.conf.org
$ sudo ln -s /home/fhuser/formhub/extras/nginx-default.conf default.conf
$ sudo /etc/init.d/nginx configtest
```

If everything is ok, nginx will respond with:

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Now restart nginx with <tt>sudo /etc/init.d/nginx restart</tt> and revisit <tt>http://127.0.0.1</tt> in a web browser.

Behold formhub in all its glory.

## 9. Install Development Tools

If you plan to do any development work on formhub, either to contribute code back to this repository, or do some hacking on your own, you should also install the <tt>requirements-dev.pip</tt> packages via pip:

```
$ sudo pip install -r /home/fhuser/formhub/requirements-dev.pip
```

## 10. Install Tools for [Amazon cloud services](http://aws.amazon.com/) (AWS)

If you plan to use AWS for your formhub server, you should consider [using the public Formhub Amazon Machine Image (AMI)](https://github.com/SEL-Columbia/formhub/wiki/How-To-Run-Your-Own-Formhub-Instances-on-Amazon-Web-Services) instead, but if you would really do all this from scratch, you should also install the corresponding packages via pip:

```
$ sudo pip install -r /home/fhuser/formhub/requirements-s3.pip  
$ sudo pip install -r /home/fhuser/formhub/requirements-ses.pip
```

Also note that the celery daemon will *not* start properly on AWS instances, even if you have executed the <tt>sudo /sbin/insserv celeryd</tt> command, earlier.

Instead, add this line to your instance's <tt>/etc/rc.local</tt> file, just above the last line (i.e., <tt>exit 0</tt>), like this:

```
# By default this script does nothing.

/etc/init.d/celeryd start 
exit 0
```
