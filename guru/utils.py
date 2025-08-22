import numpy as np
import regex as re

snap_spacing = 0.0625

def transform(pos):
    t_pos = []
    for n in pos:
        t_pos.append(n * snap_spacing)
    return np.asarray(t_pos)

def i_transform(pos):
    t_pos = []
    for n in pos:
        t_pos.append(n / snap_spacing)
    return np.asarray(t_pos)

# from https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
def rotate(p, origin: tuple[int,int] = (0, 0), degrees=0):
    angle = np.deg2rad(degrees)
    R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    o = np.atleast_2d(origin)
    p = np.atleast_2d(p)
    return np.squeeze((R @ (p.T - o.T) + o.T).T)

def calc_center(bBox):
    w = bBox[1][0] - bBox[0][0]
    h = bBox[1][1] - bBox[0][1]

    x = bBox[0][0] + (w / 2)
    y = bBox[0][1] + (h / 2)
    return [x, y]

class internal_iter:
    def __init__(self, obj, keys):
        self._obj = obj
        self._iter = iter(keys)
        self._index = 0

    def __next__(self):
        return getattr(self._obj, next(self._iter))

def create_wave(voltages, period, rise_time = 200e-12):
    """
    Create a piecewise linear voltage wave from a list of voltages which change at the rate of provided period.
    """
    v_cycle = []
    for i, v in enumerate(voltages):
        v_cycle.append((i*period, v))

    return get_tv_pairs(v_cycle, rise_time)

# given a list of (time, voltage) pairs, returns a string for a pwl stimuli
# vcycle = [(0., 3.3), (1*period, 1.5), (2*period, 3.3)]
def get_tv_pairs(v_cycle, rise_time = 200e-12):
    

    add_rt = 0
    tv_pairs = []
    for i in range(len(v_cycle)):
        t = str(v_cycle[i][0] + rise_time * add_rt)
        v = str(v_cycle[i][1])
        tv_pairs.append(t)
        tv_pairs.append(v)
        # vw[f't{i*2+1}'] = str(v_cycle[i][0] + rise_time * add_rt)
        # vw[f'v{i*2+1}'] = str(v_cycle[i][1])

        # check we arent on the last v_cycle
        if i < len(v_cycle) - 1:
            t = str(v_cycle[i+1][0])
            v = str(v_cycle[i][1])
            tv_pairs.append(t)
            tv_pairs.append(v)
            # vw[f't{i*2+2}'] = str(v_cycle[i+1][0])
            # vw[f'v{i*2+2}'] = str(v_cycle[i][1])
            add_rt = 1

    # for i, (t, v) in enumerate(tv_pairs):
    #     vw[f't{i+1}'] = t
    #     vw[f'v{i+1}'] = v
    
    return str(tv_pairs).replace('[', '').replace(']', '').replace(',', '').replace("'", '')

# convert strings like 400n to 400e-9 or 0.4u to 400e-9
def convert_str_to_num(string):
    # look for a number with or without a decimal 
    # followed by 0 or more numbers then 0 or 1 lower case or upper case letter
    res = re.findall(r'(\d+\.?\d*)([a-z]*|[A-Z]*)', string)
    num = 0
    if len(res) > 0:
        n = float(res[0][0])
        ext = res[0][1]


        if ext == 'f':
            num = n * 1e-15
        elif ext == 'p':
            num = n * 1e-12
        elif ext == 'n':
            num = n * 1e-9
        elif ext == 'u':
            num = n * 1e-6
        elif ext == 'm':
            num = n * 1e-3
        elif ext == 'k' or ext == 'K':
            num = n * 1e3
        elif ext == 'M':
            num = n * 1e6
        elif ext == 'G':
            num = n * 1e9
        elif ext == 'T':
            num = n * 1e12
        else:
            try:
                return float(string)
            except:
                print(f"Could not convert {string} to float. If this parameter is not an SI unit, ignore this error")
                return string
    else:
        return string
    
    return num

# ([pin of other instance, pin_name], direction)
class ConnPos:
    def __init__(self, external_pin, internal_pin, direction, offset=10, net_name=None, add_pin=False):
        self.external_pin = external_pin
        self.internal_pin = internal_pin
        self.direction = direction
        self.net_name = net_name
        self.add_pin = True

        if self.direction in ['above', 'up']:
            self.pos1 = external_pin.pos + [0., offset]
            self.label_offset = [0., offset/2]
        elif self.direction in ['below', 'down']:
            self.pos1 =  external_pin.pos - [0., offset]
            self.label_offset =  [0., offset/2]
        elif self.direction == 'left':
            self.pos1 =  external_pin.pos - [offset, 0.]
            self.label_offset =  [offset/2, 0.]
        elif self.direction == 'right':
            self.pos1 =  external_pin.pos + [offset, 0.]
            self.label_offset =  [offset/2, 0.]
        elif self.direction == 'upright':
            self.pos1 =  external_pin.pos + [offset, offset]
            self.label_offset =  [offset/2, offset/2]

def create_vsource(sch,
                   type,
                    pos,
                    name,
                    p_name,
                    n_name="gnd!",
                    rotation="R0"):
    
    v_src = sch.create_instance(
        "analogLib",
        type,
        pos,
        name,
        rotation
    )

    sch.create_wire(
        [v_src.pins.PLUS, [v_src.pins.PLUS.x, v_src.pins.PLUS.y + 4.0]],
        p_name,
        [1.0, 3.0],
    )

    sch.create_wire(
        [v_src.pins.MINUS, [v_src.pins.MINUS.x, v_src.pins.MINUS.y - 4.0]],
        n_name,
        [1.0, -1.5],
    )

    return v_src

def props_to_layout(props):
    new_props = props.copy()
    for dev in props:
        new_props[dev] = {}
        new_props[dev]['l'] = convert_str_to_num(props[dev]['l'])
        new_props[dev]['wt'] = convert_str_to_num(props[dev]['wt'])
        new_props[dev]['wf'] = new_props[dev]['wt']/props[dev]['nf']
        new_props[dev]['nf'] = props[dev]['nf']

        new_props[dev]['l'] *= 1e6
        new_props[dev]['wt'] *= 1e6
        new_props[dev]['wf'] *= 1e6
    return new_props

def convert_props_to_param(props):

    param = []
    param.append(['l', 'float', props['l']*1e-6])
    param.append(['w', 'float', (props['wt']/props['nf'])*1e-6])
    param.append(['nf', 'integer', props['nf']])
    param.append(['wf', 'float', (props['wt']/props['nf'])*1e-6])

    return param