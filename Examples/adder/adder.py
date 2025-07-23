import virtuosopy as vp
import numpy as np

from multiprocessing import Pool
# import multiprocess as mp
# from multiprocess import Pool

# Import PySwarms
from pyswarms.single.global_best import GlobalBestPSO

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

def create_adder(ws_name='default'):
    w = [f'w{i}' for i in range(17)]
    sch = vp.Schematic('vp_demonstration', f'AP_ADD_1_{ws_name}', ws_name, overwrite=True)

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

    sch.add_param_vars(w)
    sch.save()

    return sch

def adder_simulation(sch, period, stim_data):
    # setup stimuli
    stims = {}
    stims['A'] = {'function' : 'bit', 'data' : stim_data['A']}

    stims['B'] = {'function' : 'bit', 'data' : stim_data['B']}

    stims['Cin'] = {'function' : 'bit', 'data' : stim_data['Cin']}

    model_files = ['../../model/FinFET/14nfet.pm', '../../model/FinFET/14pfet.pm']

    s = vp.Simulator(sch, model_files)
    s.tran(f"{len(stim_data['A']) * period}")

    s.td_stim_defaults = {'val0' : 0, 'val1' : 0.8, 'period' : 20e-9, 'rise' : 1e-9, 'fall' : 1e-9}
    s.apply_stims(stims)

    s.track_net('Cin', group='Input Voltage')
    s.track_net('B', group='Input Voltage')
    s.track_net('A', group='Input Voltage')

    s.track_net('Sum_b', group='Output Voltage')
    s.track_net('Cout_b', group='Output Voltage')

    s.track_net(':pwr', 'power', 'Power')

    return s

def adder_score(s, period, stim_len):
    # get time axis of each parameter set
    # s.x is a 2D array with shape (n_parameter_sets, n_time_points)
    Tp = s.x

    # check outputs at specific times (in the center of each period)
    sample_times = np.arange(period/2, period * stim_len, period)

    # print('Time(ns)\tA\tB\tCin\tSum\tCout')

    Scores = []
    for i, t in enumerate(Tp):
        n_correct = 0
        for s_t in sample_times:
            # get the index in the waves for this sample time
            index = (np.abs(t - s_t).argmin())
            
            # this is how you access the data in each wave (ie. Voltage)
            # '/Cin' is the name of the data
            # 'y' means y-axis which is where the data is
            # 'i' is the index of the parameter set
            # [index] is the index target we calculated to be in the center of a period
            if s.waves['/Cin']['y'][i][index] >= 0.4:
                cin = 1
            else:
                cin = 0

            if s.waves['/A']['y'][i][index] >= 0.4:
                a = 1
            else:
                a = 0

            if s.waves['/B']['y'][i][index] >= 0.4:
                b = 1
            else:
                b = 0
                
            # outputs are switched since they are "bar"
            if s.waves['/Sum_b']['y'][i][index] >= 0.4:
                sum_out = 0
            else:
                sum_out = 1

            if s.waves['/Cout_b']['y'][i][index] >= 0.4:
                cout = 0
            else:
                cout = 1
            
            sum_correct = (a ^ b ^ cin)
            cout_correct = (a ^ b) & cin | (a & b)

            if sum_out == sum_correct:
                n_correct += 1
            if cout == cout_correct:
                n_correct += 1

        total_power = s.waves['/:pwr']['y'][i][index]
        # area =  
        if n_correct / (len(sample_times) * 2) != 0.75:
            Scores.append(0)
        else:
            Scores.append(-total_power)
        # print(f'{int(s_t*1e9)}\t\t{a}\t{b}\t{cin}\t{sum_out}({sum_correct})\t{cout}({cout_correct})')

    # print(f'Correct outputs: {n_correct}/{len(sample_times) * 2}')

    return Scores

from typing import override
import os

def run_sim(args):
    w, schematic, simulation_function, sim_args, score_function = args

    s = adder_simulation(schematic, *sim_args)

    p_values = {}
    for param_j in range(len(w[0])):
        p_values[f'w{param_j}'] = w[:, param_j].tolist()

    s.run(plot_in_v=False, p_values=p_values)

    if s.run_ok:
        si = adder_score(s, period, len(stim_data['A']))
    else:
        si = [0] * len(stim_data['A'])

    return si

class circuit_optimizer:
    def __init__(self, score_fn, simulation_fn, sim_args, sch, n_particles, bounds, options, n_workspaces=1):
        self.score_function = score_fn
        self.simulation_function = simulation_fn
        self.sim_args = sim_args
        self.schematic = sch
        self.n_particles = n_particles
        self.bounds = bounds
        self.options = options
        self.method = None
        self.n_workspaces = n_workspaces

    def get_score_over_workspaces(self, w):
        sims_per_workspace = len(w) // self.n_workspaces
        leftover = len(w) % self.n_workspaces

        procs_args = []

        unix_username = os.getenv('USER')

        for i in range(0, len(w) - leftover, sims_per_workspace):
            procs_args.append([w[i:i+sims_per_workspace], f'{unix_username}_{i//sims_per_workspace}'])

        if leftover > 0:
            remaining_sims_start = len(w) - leftover
            remaining_sims = leftover
            current_sim = self.n_workspaces - leftover

            while remaining_sims > 0:
                procs_args[current_sim] = [np.append(procs_args[current_sim][0], w[remaining_sims_start:remaining_sims_start+1], axis=0), procs_args[current_sim][1]]
                current_sim += 1
                if current_sim >= self.n_workspaces:
                    current_sim = 0
                remaining_sims -= 1
                remaining_sims_start += 1

        # print(args)
        # print(len(args))
        # for i in args:
        #     print(len(i[0]))

        for i, args in enumerate(procs_args):
            workspace = f'{unix_username}_{i//sims_per_workspace}'
            args.append(vp.Schematic.from_sch(self.schematic,
                                self.schematic.lib_name,
                                self.schematic.cell_name + f'_{workspace}',
                                workspace,
                                overwrite=True, verbose=False))
            # print(args[-1])
            # print(self.schematic)
            args.append(self.simulation_function)
            args.append(self.sim_args)
            args.append(self.score_function)

        with Pool(processes=self.n_workspaces) as pool:
            results = pool.map(run_sim, procs_args)

        
        mapped_results = []
        for res in results:
            for r in res[0:sims_per_workspace]:
                mapped_results.append(r)

        if leftover > 0:
            for res in results[self.n_workspaces - leftover:]:
                mapped_results.append(res[-1])
                

        return mapped_results

    def get_score(self, w):

        if self.n_workspaces > 1:
            return self.get_score_over_workspaces(w)
        
        si = run_sim([w, self.schematic, self.simulation_function, self.sim_args, self.score_function])
        return si





if __name__ == '__main__':
    period = 20e-9
    
    stim_data = {
        'A' : '01010101',
        'B' : '00110011',
        'Cin' : '00001111'
    }

    options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
    n_particles = 2

    # w = [np.ones(n_fets) * i * 10 for i in range(n_particles)]
    # print(f'Initial weights: {w}')
    # print(f'mean weights: {np.mean(w, axis=1)}')
    # get_score(w, period, stim_data)

    sch = create_adder()
    n_fets = len(sch.param_vars)
    w_min = 14e-9 * np.ones(n_fets)
    w_max = 500e-9 * np.ones(n_fets)
    bounds = (w_min, w_max)

    opt = circuit_optimizer(adder_score, adder_simulation,
                     sim_args=(period, stim_data),
                     sch=sch,
                     n_particles=n_particles,
                     bounds=bounds,
                     options=options,
                     n_workspaces=1)

    optimizer = GlobalBestPSO(n_particles=n_particles, dimensions=n_fets, options=options, bounds=bounds)
    cost, pos = optimizer.optimize(opt.get_score, iters=2)

    print(optimizer.cost_history)
    print(f'Best cost: {cost}')
    print(f'Best position: {pos}')

    