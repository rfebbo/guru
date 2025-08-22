import matplotlib.pyplot as plt
from skillbridge import Workspace

from guru import Schematic, Simulator, create_wave, ConnPos


# if the script in the launch_scripts folder was used to 
# launch virtuoso and skillbridge, the workspace id will be your unix username followed by "_0"
ws = Workspace.open(workspace_id='rfebbo_0')

# This creates (or overwrites if it exists) a schematic called example_circuit under the vp_ncsu_examples library
# If overwrite=True is not there and you try to create an instance that already exists you will get an error.
sch = Schematic(ws, 'vp_ncsu_examples', 'inverter', overwrite=True)

## create an nmos
nmos = sch.create_instance('NCSU_TechLib_FreePDK15', 'nmos', [0.,0.], 'nmos')

# apply a width, length, and model
nmos['w'] = '1u'
nmos['l'] = '1u'
nmos['model'] = 'ami06N'

# print its details
print(nmos)

# connect the body to the source
sch.create_wire([nmos.pins.S, nmos.pins.B], 'gnd!')

## create a pmos
pmos = sch.create_instance('NCSU_TechLib_FreePDK15', 'pmos', ConnPos(nmos.pins.D, 'D', 'above'), 'pmos')

# apply a width, length, and model
pmos['w'] = '1u'
pmos['l'] = '1u'
pmos['model'] = 'ami06P'

# connect the body to the source
sch.create_wire([pmos.pins.S, pmos.pins.B], 'vdd!')

# connect the gates
sch.create_wire([nmos.pins.G, pmos.pins.G])

# connect input pin
pin_In = sch.create_pin('In', 'input', ConnPos(nmos.pins.G, None, 'left', 2))
pin_Out = sch.create_pin('Out', 'output', ConnPos(nmos.pins.D, None, 'right', 2))

if sch.save():
    print('error saving')
else:
    print('Save successful')

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

s.track_pin(nmos.pins.D, group='current')

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
