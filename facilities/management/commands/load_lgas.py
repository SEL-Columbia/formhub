from django.core.management.base import BaseCommand
from optparse import make_option
from facilities.data_loader import load_lgas
import os
import subprocess

def _strings_in_list(l):
    #*args list receives a non-string param
    o = []
    for i in l:
        if isinstance(i, str):
            o.append(i)
    return o

class Command(BaseCommand):
    help = "Load the LGA data from fixtures."

    option_list = BaseCommand.option_list + (
        make_option("--inside-hup-subprocess",
                    dest="_hup_subprocess",
                    default=False,
                    action="store_true"),
        make_option("-n", "--no-spawn",
                    dest="no_spawn_process",
                    default=False,
                    action="store_true"),
    )

    def handle(self, *args, **kwargs):
        if len(args) == 0:
            raise Exception("this management command requires arguments of one or many lga ids")
        if not kwargs['no_spawn_process']:
            if not kwargs['_hup_subprocess']:
                self.start_subprocess(*args)
            else:
                self.handle_in_subprocess(*args)
        else:
            for lga in _strings_in_list(args):
                load_lgas([lga])
    
    def start_subprocess(*args):
        hup_args = ["nohup", "python", "manage.py", "load_lgas", "--inside-hup-subprocess"] + _strings_in_list(args)
        if os.path.exists('nohup.out'):
            raise Exception("nohup.out exists. Is the load already running?")
        if os.path.exists('load_script.pid'):
            with open('load_script.pid', 'r') as f:
                pid = f.read()
            raise Exception("load_script.pid exists. Is the process still running? [PID:%s]" % pid)
        pid = subprocess.Popen(hup_args).pid
        with open('load_script.pid', 'w') as f:
            f.write(str(pid))

    def handle_in_subprocess(*args):
        load_lgas(_strings_in_list(args))
        os.rename('nohup.out', 'load_script.logs')
        os.unlink('load_script.pid')