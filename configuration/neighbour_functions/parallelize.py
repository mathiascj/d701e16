from configuration.path_placers import  push_underneath
import random

def parallel_args(line, free_modules, csh):
    temp = []
    for split, m in enumerate(line):
        cm = capable_modules(m.active_w_type, free_modules)
        free_modules = list(set(free_modules) - set(csh.transport_modules))
        temp.append((m, parallel_args_helper(cm, line[split + 1:], free_modules)))

    # Check whether or not we can attach this path to a start and end and that the path has an actual length
    for r in temp:
        r_len = len(r[0].traverse_right())
        for path in r[1].copy():
            if not r_len > len(path):
                r[1].remove(path)
    result = [r for r in temp if r[0].in_left and r[1]]

    arg_list = []

    for r in result:
        for path in r[1]:
            start = r[0].in_left
            end = r[0].traverse_right_by_steps(len(path))[-1]
            arg_list.append((start, path, end))

    return arg_list



def parallel_args_helper(capable, remaining, free_modules):
    result = []
    if capable:
        """
        c = random.choice(list(capable))
        fm = free_modules.copy()
        fm.remove(c)
        temp = []

        result.append([c])
        if remaining:
            next_capable = capable_modules(remaining[0].active_w_type, fm)
            temp = parallel_args_helper(next_capable, remaining[1:], fm)
        if temp:
            for l in temp:
                result.append([c] + l)


        """
        for c in capable:
            fm = free_modules.copy()
            fm.remove(c)
            temp = []
            if remaining:
                next_capable = capable_modules(remaining[0].active_w_type, fm)
                temp = parallel_args_helper(next_capable, remaining[1:], fm)
            if temp:
                for l in temp:
                    result.append([c] + l)
            result.append([c])

    return result


def neighbours_parallelize(frontier, csh, active):
    def parallel_config_string(frontier, start, path, end, csh, direction):
        csh.make_configuration(frontier)
        t0 = csh.take_transport_module()
        t1 = csh.take_transport_module()

        for i, m in enumerate(start.traverse_right(end)[1:-1]): # check at det virker med den opdaterede traverse_right og -1
            path[i].active_w_type = m.active_w_type.copy()
        csh.current_modules += [t0, t1]
        expanded_path = [t0] + path + [t1]

        push_underneath(start, expanded_path, end, csh, direction)

        result = csh.configuration_str()

        csh.free_transport_module(t0)
        csh.free_transport_module(t1)

        return result

    csh.make_configuration(frontier)
    for m in csh.modules_in_config(frontier):
        if m.m_id in active:
            m.active_w_type = active[m.m_id]

    frontier = csh.configuration_str()

    main_line, up_lines, down_lines = csh.find_lines()

    main_args_list = parallel_args(main_line, csh.free_modules, csh)
    main_configs = []
    for args in main_args_list:
        main_configs.append(parallel_config_string(frontier, *args, csh, 'up'))
        main_configs.append(parallel_config_string(frontier, *args, csh, 'down'))

    up_configs = []
    for up in up_lines:
        args_list = parallel_args(up, csh.free_modules, csh)
        for args in args_list:
            config = parallel_config_string(frontier, *args, csh, 'up')
            up_configs.append(config)

    down_configs = []
    for down in down_lines:
        args_list = parallel_args(down, csh.free_modules, csh)
        for args in args_list:
            config = parallel_config_string(frontier, *args, csh, 'down')
            down_configs.append(config)


    return list(set(main_configs + up_configs + down_configs))


def modules_by_worktype(modules):
    """
    :param modules: list of module objects
    :return: Dict for looking up modules from work types
    """

    res = {}
    for m in modules:
        for w in m.w_type:
            res.setdefault(w, set()).add(m)
    return res


def capable_modules(worktypes, modules):
    """
    :param worktypes: list of worktypes
    :param modules: list of modules
    :return: set of modules which may perform all worktypes
    """

    d = modules_by_worktype(modules)

    if worktypes:
        res = set(modules)
    else:
        res = set()
    for w in worktypes:
        if w in d:
            res = res & d[w]
        else:
            return set()
    return res