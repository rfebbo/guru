#!/usr/bin/env python
import os
import subprocess
import sys
import re


# --- PDK / tech workspace directory to launch Virtuoso from ------------------
# Resolution order (first match wins):
#   1. GURU_PROJECT_DIR environment variable   (per-session override)
#   2. launch_scripts/project_dir.local        (per-machine, git-ignored)
#   3. default: the open FreePDK15 kit
# Copy project_dir.local.example -> project_dir.local to set your own path.
def _resolve_project_dir():
    env = os.getenv('GURU_PROJECT_DIR')
    if env:
        return os.path.expanduser(env.strip())
    local_cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_dir.local')
    if os.path.isfile(local_cfg):
        with open(local_cfg) as fh:
            for line in fh:
                line = line.split('#', 1)[0].strip()
                if line:
                    return os.path.expanduser(line)
    return os.path.expanduser('~/cadence/NCSU/FreePDK15/kit')

project_dir = _resolve_project_dir()

def main(args):
    if len(args) == 0:
        n_virtuosos_gui = 1
        n_virtuosos_hidden = 0
    elif len(args) == 2:
        n_virtuosos_gui = int(args[0])
        n_virtuosos_hidden = int(args[1])
    else:
        print('Please provide the number of Viruosos to run (with gui and without gui).')
        print('ie. Launch 1 visible virtuoso with a gui and no hidden ones')
        print('\t./launch_virtuosos_and_skillbridge.py 1 0')
        print('Launching with no arguments will launch a single session with a GUI')
        return

    unix_username = os.getenv('USER')

    n_virtuosos = n_virtuosos_gui + n_virtuosos_hidden
    if n_virtuosos < 1 or n_virtuosos > 10:
        print('limit number of instance between 1 and 10')
        return

    
    subprocess.run(['mkdir', 'skill_launch_files', '-p'])
    sb_path = subprocess.run(['skillbridge', 'path'], capture_output=True)
    sb_path = re.findall(r'.*load\((.*)\).*', str(sb_path.stdout))[0]

    print(f'Using {sb_path} as skillbridge path\n')
    
    python_path = str(subprocess.run(['which', 'python'], capture_output=True).stdout)[2:-3]
    subprocess.run([f'cd {project_dir}; rm ./log_files/*'], shell='/bin/bash', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for tid in range(n_virtuosos):
        
        skill_filename = f'/home/{unix_username}/cadence/guru/launch_scripts/skill_launch_files/start{tid}.il'
        with open(skill_filename, 'w') as f:
            f.write(f'load({sb_path})\n')
            f.write(f'pyStartServer ?id "{unix_username}_{tid}" ?python "LD_LIBRARY_PATH= {python_path}"\n')
            f.write('load("~/cadence/guru/launch_scripts/CCSinvokeCdfCallbacks.il")\n')

        
        if n_virtuosos_hidden > 0:
            subprocess.run([f'cd {project_dir}; source ./toolsenv; virtuoso -nograph -restore {skill_filename} &'], shell='/bin/bash', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            n_virtuosos_hidden -= 1
        elif n_virtuosos_gui > 0:
            subprocess.run([f'cd {project_dir}; source ./toolsenv; virtuoso -restore {skill_filename} &'], shell='/bin/bash')
            n_virtuosos_gui -= 1

        print(f'launched virtuoso with skillbridge with a workspace id: {unix_username}_{tid}')

if __name__ == '__main__':

    args = sys.argv[1:]
    main(args)
    
    
