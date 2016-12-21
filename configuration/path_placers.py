def connect_module_list(list, direction='right'):
    for i, m in enumerate(list):
        if i + 1 < len(list):
            # Dynamically sets direction
            setattr(m, direction, list[i + 1])


def vertical_sequence(initial, counter, grid, inverted_grid, direction, csh):
    """
    Calculates a vertical sequence for counter steps
    :param initial: Module from which sequence starts
    :param counter: Number of steps upwards
    :param grid: dict for module to position
    :param inverted_grid: dict for position to module
    :param direction: If true sequence goes upwards. If false sequence goes downwards.
    :param csh: config_string_handler
    :return:
    """

    # Picks lambda function to search up or downwards based on direction
    if direction:
        f = lambda x: x + 1
    else:
        f = lambda x: x - 1

    current = initial
    sequence = [initial]
    while 0 < counter:
        x, y = grid[current]
        next_pos = (x, f(y))
        # If there's already a module here we can move through it
        if next_pos in inverted_grid:
            next_mod = inverted_grid[next_pos]
        # if there is not a module, we append with a transport
        else:
            next_mod = csh.take_transport_module()

        sequence.append(next_mod)
        current = next_mod
        counter -= 1

    return sequence


def push_underneath(start, path, end, csh, direction): #TODO: Opater shadows and shit!
    def find_conflicting_lines(mods):
        # Find all lines containing the conflicting modules.
        lines = []
        for mod in mods:
            if mod not in [y for x in lines for y in x]:  # Flattens multidim list
                lines.append(mod.get_line())
        return lines

    def update_pos(mod, grid, direction):
        """
        Pushes module up by one.
        Returns whatever module that now needs to be evicted.
        """
        if direction:
            f = lambda x: x + 1
        else:
            f = lambda x: x - 1

        pos = grid[mod]
        new_pos = (pos[0], f(pos[1]))
        conflict = None

        for m, p in grid.items():
            if new_pos == p:
                conflict = m
                break

        grid[mod] = new_pos
        return conflict

    def move_line(line, grid, direction):
        conflicts = []

        # Moves line one up, collecting any conflicts
        for mod in line:
           conflict = update_pos(mod, grid, direction)
           if conflict:
               conflicts.append(conflict)

        # Find each line that are in conflict and move it up
        lines = find_conflicting_lines(conflicts)
        for l in lines:
            grid = move_line(l, grid, direction)

        return grid

    def reconnect(mod, grid, inverted_grid, direction, csh):
        if direction:
            dir_attribute = 'up'
        else:
            dir_attribute = 'down'

        mod_neighbour = getattr(mod, dir_attribute)

        length = abs(grid[mod][1] - grid[mod_neighbour][1])
        if 1 < length:
            counter = length - 1
            sequence = vertical_sequence(mod, counter, grid, inverted_grid, direction, csh)
            sequence.append(mod_neighbour)
            connect_module_list(sequence, dir_attribute)

    grid = csh.make_grid(csh.main_line[0])

    # Lay down path on same line as start.
    # Begins conflict.
    connect_module_list(path, 'right')
    pos = grid[start]
    for mod in path:
        grid[mod] = pos
        pos = (pos[0] + 1, pos[1])

    # Updates grid to get the path to move up. Cascades.
    grid = move_line(path, grid, direction)

    inverted_grid = {v: k for k, v in grid.items()}  # Get modules from position

    # Any modules vertically disconnected from each other are reconnecte
    for mod, pos in grid.items():

        # See if the above module is still reachable
        if mod.up:
            reconnect(mod, grid, inverted_grid, True, csh)

        # See if below module is still reachable
        if mod.down:
            reconnect(mod, grid, inverted_grid, False, csh)


    # Inserts path on line now that there is room
    if direction:
        dir1 = "up"
        dir2 = "down"
    else:
        dir1 = "down"
        dir2 = "up"

    if start:
        setattr(start, dir1, path[0])

    if end:
        setattr(path[-1], dir2, end)

    # Updates booleans
    start.is_start = True
    end.is_end = True



def push_around(start, path, end, shadow, csh):
    """
    Searches above and below already sat lines to find room.
    When room found it places down path.
    :param start: Point at which path should start on main line
    :param path:  Path we wish to branch out
    :param end: Point at which path should end on main line
    :param shadow: Sequence of modules left on main line after branch out
    :param csh: config_string_handler object
    :return:
    """

    def get_push_length(remaining, grid, inverted_grid, direction):
        """
        Finds how long we should push our path in a given direction to place it.
        :param remaining: Sequence of modules left on main line after branch out
        :param grid: Grid describing for each module where it is placed
        :param inverted_grid: Grid describing for each position, what module is placed there
        :param direction: If True we search upwards, if False we search downwards
        :return:
        """

        # Positions of all modules in remaining
        pos_on_line = [grid[x] for x in remaining]

        # Picks lambda function to search up or downwards based on direction
        if direction:
            f = lambda x: x + 1
        else:
            f = lambda x: x - 1

        # Counts up a counter until we can see no more placed modules by moving in our direction.
        counter = 0
        while True:
            # Get all positions above the currently selected positions
            pos_on_line = [(x, f(y)) for x, y in pos_on_line if (x, f(y)) in inverted_grid]
            if pos_on_line:
                counter += 1
            else:
                break

        return counter

    grid = csh.make_grid(shadow[0])  # Get positions from modules, except for those in path

    inverted_grid = {v: k for k, v in grid.items()}  # Get modules from position

    # Find length we have to move path upwards
    up_length = get_push_length(shadow, grid, inverted_grid, True)

    # Find length we have to move path downwards
    down_length = get_push_length(shadow, grid, inverted_grid, False)

    # Set length and direction in which to push the path
    if up_length <= down_length:
        length = up_length
        direction = True
        branch_out_direction = 'up'
        branch_in_direction = 'down'
    else:
        length = down_length
        direction = False
        branch_out_direction = 'down'
        branch_in_direction = 'up'

    # Connect path together
    connect_module_list(path, 'right')

    if start:
        # Connect from a start point to the path
        out_branch = vertical_sequence(start, length, grid, inverted_grid, direction, csh)
        out_branch.append(path[0])
        connect_module_list(out_branch, branch_out_direction)

    if end:
        # Connect from a end point to the path
        in_branch = vertical_sequence(end, length, grid, inverted_grid, direction, csh)
        in_branch.append(path[-1])
        in_branch.reverse()
        connect_module_list(in_branch, branch_in_direction)


    # Updates booleans
    if start:
        start.is_start = True
    if end:
        end.is_end = True

    for m in shadow:
        m.shadowed = True
