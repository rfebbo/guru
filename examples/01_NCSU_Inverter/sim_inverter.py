from guru import Simulator, Schematic, create_wave
from skillbridge import Workspace
import matplotlib.pyplot as plt

ws = Workspace.open(workspace_id='rfebbo_0')

sch = Schematic(ws, 'vp_ncsu_examples', 'inverter')
exit()
# Setup Simulator
print('Setting up Simulation...')
model_files = ['../../model/ami06/ami06P.m', '../../model/ami06/ami06N.m']

# simulate for 100ns
s = Simulator(sch, model_files)
s.tran('20n')

# setup stimuli
stims = {}

# Piecewise linear voltage stimulus 
stims['In'] = {'function' : 'pwl', 'wave' : create_wave([0.0, 5], 10e-9, 1e-9)}

# DC stimulus
stims['vdd!'] = {'function' : 'dc', 'voltage' : 5}
stims['gnd!'] = {'function' : 'dc', 'voltage' : 0.0}

# apply the stims
s.apply_stims(stims)

s.track_net('In')
s.track_net('Out')

s.track_pin(sch['nmos'].pins.D, group='current')

s.run(plot_in_v=False)

s.plot(save='images/simulation.png')

# create a VTC

x = s.waves['/In']['y']
y = s.waves['/Out']['y']

fig, ax = plt.subplots(1,1,figsize=(5,4), dpi=200)
plt.xlabel('Input (V)')
plt.ylabel('Output (V)')
plt.plot(x,y)
plt.tight_layout()
plt.savefig('images/vtc.png')
plt.show()

sch.close()