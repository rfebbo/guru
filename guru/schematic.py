from .instance import _Inst, _Pin
from .utils import snap_spacing, transform, convert_str_to_num, ConnPos

from skillbridge import Workspace
import numpy as np

class Schematic:
    def __init__(self, workspace : Workspace, lib_name, cell_name, overwrite=False, verbose=True):
        self.ws = workspace

        if self.ws.db.full_lib_path(lib_name) == None:
            self.lib_id = self.ws.db.create_lib(lib_name)
            
            print(f'Created library {lib_name}')
        
        if overwrite:
            self.cv = self.ws.db.open_cell_view_by_type(lib_name, cell_name, "schematic",
                                          "schematic", "w")
        else:
            self.cv = self.ws.db.open_cell_view_by_type(lib_name, cell_name, "schematic",
                                          "schematic", "a")
            self.load_schematic_contents()


        self.lib_name = lib_name
        self.cell_name = cell_name
        self.instances = {}
        
        self.instances_params = []
        self.wires = []
        self.notes = []
        self.pins = []

        self.verbose = verbose

        self.param_vars = []
        self.cdf_ignore = []

    def load_schematic_contents(self):
        # print(self.ws.db)
        self.ws.db.write_skill_with_lib(self.cv, 'schematic.il', 'w', '6.1')
        # self.ws.sch.attach_lib_to_package_tech(self.lib_name)

    def delete_cell_view(self):
        """
        Delete the schematic from the database.
        """
        if self.verbose:
            print(f"Deleting {self.lib_name}.{self.cell_name} from {self.ws.name}")
    
        self.ws.dd.delete_obj(self.ws.dd.get_obj(self.lib_name, self.cell_name, "schematic"))

    def __dict__(self):
        s = {}

        s['lib_name'] = self.lib_name
        s['cell_name'] = self.cell_name
        s['instances_params'] = self.instances_params

        instances = {}
        for inst in self.instances:
            inst_dict = {}
            for ap in self.instances[inst].applied_params:
                inst_dict[ap] = self.instances[inst].applied_params[ap]
            instances[inst] = inst_dict

        s['instances'] = instances
        s['wires'] = self.wires
        s['notes'] = self.notes
        s['pins'] = self.pins
        s['param_vars'] = self.param_vars
        s['cdf_ignore'] = self.cdf_ignore

        return s

    @classmethod
    def from_dict(cls, d, lib_name, cell_name, ws_name="default", overwrite=True, verbose=False):
        """
        Create a new schematic object from a dictionary representation.
        """


        new_schematic = cls(lib_name, cell_name, ws_name=ws_name, overwrite=overwrite, verbose=verbose)

        for instances_params in d['instances_params']:
            inst = _Inst(new_schematic.ws, new_schematic.cv, *instances_params)

            new_schematic.instances[instances_params[3]] = inst

            if instances_params[3] in d['instances']:
                for ap, value in d['instances'][instances_params[3]].items():
                    inst[ap] = value
                
            new_schematic.instances_params.append(instances_params)

        for pin_params in d['pins']:
            inputCVId = new_schematic.ws.db.open_cell_view("basic", pin_params[0], "symbol")
            new_schematic.ws.sch.create_pin(new_schematic.cv, inputCVId, *pin_params[1:])
            new_schematic.pins.append(pin_params)

        for (wire_params, label_params) in d['wires']:
            mode, arg2, pos, snap_spacing, snap_spacing, arg6 = wire_params
            w = new_schematic.ws.sch.create_wire(new_schematic.cv, mode, arg2, pos, snap_spacing,
                                                snap_spacing, arg6)
            if label_params is not None:
                new_schematic.ws.sch.create_wire_label(new_schematic.cv, w[0], *label_params)

            new_schematic.wires.append((wire_params, label_params))

        for note_params in d['notes']:
            new_schematic.ws.sch.create_note_label(new_schematic.cv, *note_params)
            new_schematic.notes.append(note_params)

        new_schematic.param_vars = d['param_vars'].copy()
        new_schematic.cdf_ignore = d['cdf_ignore'].copy()

        new_schematic.save()


        return new_schematic

    @classmethod
    def from_sch(cls, sch, lib_name, cell_name, ws_name, overwrite=False, verbose=True):
        """
        Create a new schematic object from an existing schematic object.
        """

        new_schematic = cls(lib_name, cell_name, ws_name=ws_name, overwrite=overwrite, verbose=verbose)

        for instances_params in sch.instances_params:
            inst = _Inst(new_schematic.ws, new_schematic.cv, *instances_params)

            new_schematic.instances[instances_params[3]] = inst
            new_schematic.instances_params.append(instances_params)

        for pin_params in sch.pins:
            inputCVId = new_schematic.ws.db.open_cell_view("basic", pin_params[0], "symbol")
            new_schematic.ws.sch.create_pin(new_schematic.cv, inputCVId, *pin_params[1:])
            new_schematic.pins.append(pin_params)

        for (wire_params, label_params) in sch.wires:
            mode, arg2, pos, snap_spacing, snap_spacing, arg6 = wire_params
            w = new_schematic.ws.sch.create_wire(new_schematic.cv, mode, arg2, pos, snap_spacing,
                                                snap_spacing, arg6)
            if label_params is not None:
                new_schematic.ws.sch.create_wire_label(new_schematic.cv, w[0], *label_params)

            new_schematic.wires.append((wire_params, label_params))

        for note_params in sch.notes:
            new_schematic.ws.sch.create_note_label(new_schematic.cv, *note_params)
            new_schematic.notes.append(note_params)

        new_schematic.param_vars = sch.param_vars.copy()
        new_schematic.cdf_ignore = sch.cdf_ignore.copy()

        new_schematic.save()

        return new_schematic


    def create_instance(self, lib_name, cell_name, pos, name, rot='R0'):
        """
        Instantiate a component in the schematic

        Parameters
        ----------
        lib_name : string
            library for the component (eg. 'analoglib')
        cell_name : string
            cell name for the component (eg. 'nmos4')
        pos : [float, float] or ConnPos
            position of the component (eg. [0., 0.] or ConnPos(nmos.pins.D, 'MINUS', 'above') )
        name : string
            instance name for the component (eg. 'MN1')
        rot : string
            rotation (eg. 'R90')
        """
        inst: _Inst = None # type: ignore

        inst_params = None

        if isinstance(pos, ConnPos):
            inst = _Inst(self.ws, self.cv, lib_name, cell_name, pos.pos1, name, rot)
            inst_params = (lib_name, cell_name, pos.pos1, name, rot)
            self.create_wire([pos.external_pin, inst.pins[pos.internal_pin]], net_name=pos.net_name, label_offset=pos.label_offset)
        elif isinstance(pos, list) or isinstance(pos, np.ndarray):
            if len(pos) == 2:
                inst = _Inst(self.ws, self.cv, lib_name, cell_name, pos, name, rot)
                inst_params = (lib_name, cell_name, pos, name, rot)
        else:
            print('Pos parameter must be:')
            print('\tan xy coordinate represented by an array of length 2')
            print('\ta ConnPos')
            print("\t (eg. [0., 0.] or ConnPos(nmos.pins.D, 'MINUS', 'above') )")
            print(f"\t {pos}")
            return inst

        self.instances[name] = inst
        self.instances_params.append(inst_params)
        return inst

    def create_wire(self, positions, net_name=None, label_offset=None, mode='route'):

        # transform into virtuoso coords
        pos = []
        for i in range(len(positions)):
            if isinstance(positions[i], _Pin):
                pos.append(list(transform(positions[i].pos)))
            elif 'base_name' in dir(
                    positions[i]) and positions[i].base_name[:3] == 'PIN':
                pos.append(positions[i].xy)
            else:
                pos.append(list(transform(positions[i])))

        w = self.ws.sch.create_wire(self.cv, mode, "full", pos, snap_spacing,
                                    snap_spacing, 0.0)
        
        # if net_name == 'Sum_b':
        #     print(f'Creating wire with net name: {net_name} at positions: {pos}')
        #     print(f'Wire params: {w}')
        #     print(f'wire dir {dir(w[0])}')
        #     print(f'wire dir {w[0].points}')
        #     print(f'wire dir {w[1].points}')
        #     print(f'wire dir {w[2].points}')
        #     print(self.ws.sch.create_wire)
        #     raise

        points = []
        if w is not None:
            for wi in w:
                points.append(wi.points)
        
        print(points)

        wire_params = (mode, "full", pos.copy(), snap_spacing, snap_spacing, 0.0)
        
        label_params = None
        if net_name != None:
            l_pos = pos[0]
            if label_offset != None:
                label_offset = transform(label_offset)
                l_pos = np.asarray(l_pos) + np.asarray(label_offset)
                l_pos = list(l_pos)
            self.ws.sch.create_wire_label(
                self.cv,
                w[0],
                l_pos,
                net_name,
                "upperLeft",
                "R0",
                "fixed",
                snap_spacing,
                None,
            )
            label_params = (l_pos, net_name, "upperLeft", "R0", "fixed", snap_spacing, None)
            

        
        self.wires.append((wire_params, label_params))
        # self.wires.append(w)      
        return w


    def create_note(self, note, pos, size=0.125):
        pos = transform(pos)
        self.ws.sch.create_note_label(self.cv, list(pos), note, "lowerLeft",
                                      "R0", "fixed", size, "normalLabel")
        
        note_params = (list(pos), note, "lowerLeft", "R0", "fixed", size, "normalLabel")
        self.notes.append(note_params)

    def create_pin(self, name, direction, pos, rot='R0'):
        if isinstance(pos, ConnPos):
            pin_pos = pos.pos1
            pos.external_pin.netname = name
            self.create_wire([pos.external_pin, pin_pos], net_name=pos.net_name, label_offset=pos.label_offset)
            if direction == 'wire':
                return
            pos = pin_pos

        pos = transform(pos)
        cell_name = None
        if direction == "input":
            cell_name = "ipin"
        elif direction == "output":
            cell_name = "opin"
        elif direction == "inputOutput":
            cell_name = "iopin"
        else:
            if self.verbose:
                print(f"Creation of Pin {name} Failed! \ndirection should be one of: [input, output, inputOutput]. got {direction}")
            return 0

        inputCVId = self.ws.db.open_cell_view("basic", cell_name, "symbol")
        p_id = self.ws.sch.create_pin(self.cv, inputCVId, name, direction,
                                      None, list(pos), rot)
        
        pin_params = (cell_name, name, direction, None, list(pos), rot)
        self.pins.append(pin_params)

        return p_id

    def add_param_vars(self, vars):
        self.param_vars += vars

    def add_cdf_ignore(self, vars):
        self.cdf_ignore += vars

    def redraw(self):
        self.ws.hi.redraw()

    def do_cdf_callbacks(self):

        # self.ws['CCSinvokeCdfCallbacks'](f"{self.cv} ?callInitProc t ?useInstCDF t")
        self.ws['CCSinvokeCdfCallbacks'](self.cv, debug=True, callInitProc=True,useInstCDF=True)
        # self.ws['CCSinvokeCdfCallbacks'](self.cv, addFormFields=True)
        # self.ws['CCSinvokeCdfCallbacks'](self.cv, debug=False, order=['wt', 'wf']) #'l', 'wt', 
        # self.ws['CCSinvokeCdfCallbacks'](self.cv, debug=True)

        # CDF callbacks use the user applied parameters to calculate the actual parameters
        # Sometimes user applied parameters don't stick
        # let the user know if that happens:
        rv = 0
        for _, i in self.instances.items():
            for a_p_name, a_p_value in i.applied_params.items():
                if a_p_value == '' or a_p_value in self.param_vars or a_p_value in self.cdf_ignore or a_p_name == 'model':
                    break
                
                calc_val = i.params[a_p_name].value
                app_val = a_p_value

                # convert strings to floats for comparison
                if isinstance(app_val, str):
                    app_val = convert_str_to_num(app_val)

                if isinstance(calc_val, str):
                    calc_val = convert_str_to_num(calc_val)

                if isinstance(app_val, str):
                    try:
                        if calc_val != app_val:
                            if self.verbose:
                                print(f'Error: Calculated Parameter is not equal to Applied Parameter for {a_p_name} on {i.name}.')
                                print(f'{i.params[a_p_name].value} != {a_p_value}')
                                print(f'calc_val: {type(calc_val)}, app_val: {type(app_val)}')
                            rv = 1
                    
                        elif not np.isclose(calc_val, app_val):
                            if self.verbose:
                                print(f'Error: Calculated Parameter is not close to Applied Parameter for {a_p_name} on {i.name}.')
                                print(f'{i.params[a_p_name].value} != {a_p_value}')
                            rv = 1
                    except:
                        if calc_val == app_val:
                            continue
                        else:
                            print(f'Could not convert {calc_val} or {app_val} to float')

        return rv

    def save(self, do_callbacks=True):
        rv = 0
        if do_callbacks and self.do_cdf_callbacks():
            rv = 1

        self.ws.sch.check(self.cv)
        self.ws.db.save(self.cv)
        return rv
    

    def close(self, purge=True):
        if purge:
            self.ws.db.purge(self.cv)
        self.ws.close()
        
