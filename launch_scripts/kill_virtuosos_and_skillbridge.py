#!/usr/bin/env python
import os
import subprocess
import sys

def main():

    unix_username = os.getenv('USER')
    subprocess.run(f"kill $(ps aux | egrep '(virtuoso -nograph -restore)|(skillbridge/server/python_server.py)|(virtuoso -restore)|(virtuoso -nographE -restore)' | grep {unix_username} | awk '{{print $2}}')", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(f"rm -rf /tmp/skill-server-{unix_username}*", shell=True)
    subprocess.run(f"rm -rf /tmp/crashReport*{unix_username}*", shell=True) # :/

if __name__ == '__main__':

    main()
    