import guru as vp
import numpy as np

# store the nmoses and pmoses so we can reference them for routing wires
pmoses = []
nmoses = []
# creates a stack of nmoses and pmoses
def stack(sch : vp.Schematic, pos, np, nn, labels, stack_num, width_iter):
    ps = []
    ns = []

    if np > 0:    
        p = sch.create_instance('analogLib', 'pmos4', pos, f'pm{stack_num}_0')
        sch.create_wire([p.pins.G,p.pins.G.pos + [-1., 0.]], labels[0])
        sch.create_wire([p.pins.B,p.pins.B.pos + [1., 0.]], 'vdd!')
        p['model'] = 'pfet'
        p['l'] = '10n'
        p['w'] = next(width_iter)
        ps.append(p)
        for i in range(1, np):
            p = sch.create_instance('analogLib', 'pmos4', vp.ConnPos(ps[-1].pins.D, 'S', 'below'), f'pm{stack_num}_{i}')
            
            sch.create_wire([p.pins.G,p.pins.G.pos + [-1., 0.]], labels[np])
            sch.create_wire([p.pins.B,p.pins.B.pos + [1., 0.]], 'vdd!')
            p['model'] = 'pfet'
            p['w'] = next(width_iter)
            ps.append(p)

        sch.create_wire([ps[0].pins.S, ps[0].pins.S.pos + [0.,2.]], 'vdd!')

    if nn > 0:
        n = sch.create_instance('analogLib', 'nmos4', vp.ConnPos(ps[-1].pins.D, 'D', 'below'), f'nm{stack_num}_{0}')
        sch.create_wire([n.pins.G,n.pins.G.pos + [-1.,0.]], labels[np])
        sch.create_wire([n.pins.B,n.pins.B.pos + [1.,0.]], 'gnd!')
        n['model'] = 'nfet'
        n['l'] = '10n'
        n['w'] = next(width_iter)
        ns.append(n)
        for i in range(1, nn):
            n = sch.create_instance('analogLib', 'nmos4', vp.ConnPos(ns[-1].pins.S, 'D', 'below'), f'nm{stack_num}_{i}')
            sch.create_wire([n.pins.G,n.pins.G.pos + [-1.,0.]], labels[i+np])
            sch.create_wire([n.pins.B,n.pins.B.pos + [1.,0.]], 'gnd!')
            n['model'] = 'nfet'
            n['w'] = next(width_iter)
            ns.append(n)

        sch.create_wire([ns[-1].pins.S, ns[-1].pins.S.pos + [0.,-2.]], 'gnd!')


    return ps, ns

w = np.random.uniform(low=14e-9, high=14-9, size=17)
w = [f'{wi:.3}' for wi in w]

width_iter = iter(w)
        

sch = vp.Schematic('vp_demonstration', 'AP_ADD_1', overwrite=True)


# store the nmoses and pmoses so we can reference them for routing wires
pmoses = []
nmoses = []

width_iter = iter(w)
        
# create the 5 stacks
ps, ns = stack(sch, [0.,0.], 2 , 2, ['B', 'Cin', 'Cin', 'A'], 0, width_iter)
pmoses += ps
nmoses += ns

ps, ns = stack(sch, [10.,0.], 2 , 1, ['B', 'A', 'B'], 1, width_iter)
pmoses += ps
nmoses += ns

ps, ns = stack(sch, [20.,0.], 2 , 2, ['A', 'Cout_b', 'Cout_b', 'Cin'], 2, width_iter)
pmoses += ps
nmoses += ns

sch.create_wire([pmoses[1].pins.D,pmoses[-1].pins.G], 'Cout_b')

ps, ns = stack(sch, [30.,0.], 1, 0, ['B'], 3, width_iter)
pmoses += ps
nmoses += ns

sch.create_wire([pmoses[-1].pins.D,pmoses[-3].pins.D])

ps, ns = stack(sch, [40.,-15.], 1, 3, ['Cin', 'Cin', 'A', 'B'], 4, width_iter)
pmoses += ps
nmoses += ns

sch.create_wire([nmoses[-5].pins.D,pmoses[-1].pins.D], 'Sum_b')

# create vdd
V_VDD_0V800 = vp.create_vsource(sch, 'vdc', [-15., -20.], 'V_VDD_0V800', 'vdd!', n_name='gnd!')
V_VDD_0V800['vdc'] = '0.8'

# add pins
pin_A = sch.create_pin('A', 'input', vp.ConnPos(nmoses[1].pins.G, None, 'left', 2))
pin_B = sch.create_pin('B', 'input', vp.ConnPos(pmoses[0].pins.G, None, 'left', 2))
pin_Cin = sch.create_pin('Cin', 'input', vp.ConnPos(pmoses[1].pins.G, None, 'left', 2))

pin_Cout_b = sch.create_pin('Cout_b', 'output', vp.ConnPos(pmoses[5].pins.G, None, 'above', 8), 'R90')
pin_Sum_b = sch.create_pin('Sum_b', 'output', vp.ConnPos(pmoses[-1].pins.D, None, 'right', 2))

# add capacitors
cout_cap = sch.create_instance('analogLib', 'cap', [-15., -40.], 'cout_cap')
cout_cap['c'] = '1f'
sch.create_wire([cout_cap.pins.PLUS, cout_cap.pins.PLUS.pos + [0., 2.]], 'Cout_b' )
sch.create_wire([cout_cap.pins.MINUS, cout_cap.pins.MINUS.pos + [0., -2.]], 'gnd!' )

sum_b_cap = sch.create_instance('analogLib', 'cap', [-15., -55.], 'sum_b_cap')
sum_b_cap['c'] = '1f'
sch.create_wire([sum_b_cap.pins.PLUS, sum_b_cap.pins.PLUS.pos + [0., 2.]], 'Sum_b' )
sch.create_wire([sum_b_cap.pins.MINUS, sum_b_cap.pins.MINUS.pos + [0., -2.]], 'gnd!' )

sch.save()

# setup stimuli
period = 20e-9

A_stim =    '01010101'
B_stim =    '00110011'
Cin_stim =  '00001111'

stims = {}
stims['A'] = {'function' : 'bit', 'data' : A_stim}

stims['B'] = {'function' : 'bit', 'data' : B_stim}

stims['Cin'] = {'function' : 'bit', 'data' : Cin_stim}

model_files = ['../../model/FinFET/14nfet.pm', '../../model/FinFET/14pfet.pm']

s = vp.Simulator(sch, model_files)
s.tran(f"{len(stims['A']['data']) * period}", 'conservative')


s.td_stim_defaults = {'val0' : 0, 'val1' : 0.8, 'period' : 20e-9, 'rise' : 1e-9, 'fall' : 1e-9}
s.apply_stims(stims)

s.track_net('Cin', group='Input Voltage')
s.track_net('B', group='Input Voltage')
s.track_net('A', group='Input Voltage')

s.track_net('Sum_b', group='Output Voltage')
s.track_net('Cout_b', group='Output Voltage')

s.track_pin(sch.instances['V_VDD_0V800'].pins['PLUS'], 'current', 'Current')


s.run()


total_power = np.sum(s.waves['/V_VDD_0V800/PLUS']['y'])
print(f'Total power consumption: {total_power:.3f} W')

s.plot()

sch.close()