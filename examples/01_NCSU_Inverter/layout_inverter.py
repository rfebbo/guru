import guru as vp

lt = vp.layout('vp_NCSU_examples', 'inverter', overwrite=True)

nmos2 = lt.create_instance('dgnfet', 'nmos2' + name_tag, pos + [-props['nmos2']['l']/2- 1.5, nm_memr_dist-0.3], 'R180', props['nmos2'])
