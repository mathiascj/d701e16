from configuration.path_placers import connect_module_list, push_around, push_underneath
from random import choice


def anti_serialize(start, path, end, csh):
    """
    Creates an anti-serialized configuration string
    :param start: start module on main line
    :param path: sequence of modules to anti serialize
    :param end: end module on main line
    :param csh: configuration_string_handler_object
    :return: A string representing the new configuration
    """

    def remaining_modules(modules, path):
        """
        Calculates the sequence of modules on main line segment after anti-serialization
        :param modules: Original modules on main line segment
        :param path: The sequence of modules we wish to anti-serialize
        :return: Sequence of modules describing the new main line segment
        """
        remaining = []
        for m in modules:
            # In the case that the module is not in path
            if m not in path:
                remaining.append(m)

            # If the module is in path, but is also shadowed it has to be replaced with a transport.
            elif m.shadowed:
                remaining.append(csh.take_transport_module())

        return remaining

    # Calculates the modules of the main line segment touched by the anti-serialization
    if start and end:
        mods = start.traverse_right(end)
    elif start:
        mods = start.traverse_right()
    elif end:
        mods = end.traverse_in_left()
    else:
        raise RuntimeError('Both start and end cant be empty')

    # Gets sequence of modules remaining on main line segment
    remaining = remaining_modules(mods, path)

    # Remember how to connect main line segment to main line again
    start_connector = None
    end_connector = None
    if start:
        start_connector = start.in_left

    if end:
        end_connector = end.right

    # Clear the connections of all modules horizontally
    for m in mods:
        m.horizontal_wipe()

    if start and end:
        # If remaining is longer than path, we extend path with transports
        while len(remaining) > len(path):
            path.append(csh.take_transport_module())

        # When path is too long, append transports to main line
        end = remaining[-1]
        remaining.remove(end)
        while len(remaining) < len(path) - 1:
            remaining.append(csh.take_transport_module())
        remaining.append(end)

    # Reconnect original line
    connect_module_list(remaining, 'right')
    if start_connector:
        start_connector.right = start
    if end_connector:
        end.right = end_connector

    # Set up shadow. The sequence of modules on main line which the path projects down on.
    if start and end:
        shadow = remaining

    elif start:
        shadow = start.traverse_right_by_steps(len(path) - 1)

    elif end:
        shadow = end.traverse_in_left_by_steps(len(path) - 1)

    # Places down path where possible
    push_around(start, path, end, shadow, csh)

    csh.main_line = remaining
    return csh.configuration_str()


def neighbours_anti_serialized(frontier, csh, active):
    """
    Gets all possible anti_serializations, when trying to split out a random recipe from main line
    :param frontier: Configuration string, which we wish to find neighbours for
    :param csh: config_string_handler object
    :param active: active dict
    :return: A list of strings, each representing a neighbouring configuration
    """

    csh.make_configuration(frontier)
    for m in csh.modules_in_config(frontier):
        if m.m_id in active:
            m.active_w_type = active[m.m_id]

    # Get Main line
    main_line, _, _ = csh.find_lines()

    # Choose random recipe to anti-serialize
    recipe = choice(csh.recipes)
    r = set(recipe.keys())
    r_bar = set()
    for rec in csh.recipes:
        if rec != recipe:
            r_bar |= set(rec.keys())

    K = {m for m in csh.current_modules if any({p in r and p in r_bar for p in m.active_w_type})}
    beta = {m for m in csh.current_modules if all({p in r and p not in r_bar for p in m.active_w_type})}

    neighbour_args = []
    S = None
    E = None
    B = []
    
    for mod in main_line:
        if mod in K and not E:
            E = mod
            if B:
                neighbour_args.append([S, B, E, csh])
            S = E
            B = []
            E = None
        elif mod in beta:
            B.append(mod)

    if S and B:
        neighbour_args.append([S, B, E, csh])
            
    neighbours = []
    for n in neighbour_args:
        # Only call neighbours, where we do not remove starts and ends of other branches
        path = n[1]
        if not any(x.is_start or x.is_end for x in path):
            neighbours.append(anti_serialize(*n))

    return neighbours