import re
from copy import deepcopy

class ConfigStringHandler:
    def __init__(self, recipes, all_modules, transport_module, initial_configuration=""):
        self.all_modules = all_modules
        self.recipes = recipes
        self.transport_module = transport_module

        self.free_modules = all_modules.copy()

        self.current_modules = []

        self.free_transporters = []
        self.transport_modules = []
        self.main_line = []

        self.module_dictionary = {m.m_id: m for m in all_modules}
        self.recipe_dictionary = {r.name: r for r in recipes}


        self.transport_id = 0

        if initial_configuration:
            self.make_configuration(initial_configuration)

    def configuration_str(self):
        if self.current_modules:
            configuration = self.current_modules[0].find_connected_modules()
            configuration.sort(key=lambda m: m.m_id)        # Sorts the list based on m_id

            R = [r.recipe_str() for r in self.recipes]
            M = [m.module_str() for m in configuration]
            ML = ','.join(map((lambda m: m.m_id), self.main_line))

            return "$".join(R) + "|" + ':'.join(M)  + '|' + ML
        else:
            return ""

    def make_configuration(self, configuration_str):
        if not isinstance(configuration_str, str):
            raise ValueError("configuration_str should be a string!")
        self.current_modules = []
        self.reset_modules()

        S = configuration_str.split(sep="|")
        R = S[0].split(sep='$')
        for rs in R:
            split1 = rs.find('@')
            split2 = rs.find('&')

            name = rs[:split1]
            start_module = rs[split1 + 1:split2]
            start_direction = int(rs[split2 + 1:])

            self.recipe_dictionary[name].start_module = start_module
            self.recipe_dictionary[name].start_direction = start_direction

        M = S[1].split(sep=':')
        for ms in M:
            m_id = re.search('(.*)(?=\{)', ms).group(0)  # (?=...) is a lookahead assertion
            active_w_type = set(re.search('.*\{(.*)\}.*', ms).group(1).split(sep=','))
            temp = re.search('.*\[(.*)\].*', ms).group(1).split(sep=',')
            connections = [self.module_dictionary[conn_id] if conn_id != '_' else None for conn_id in temp]
            booleans = re.search('.*\](.*)', ms).group(1)


            module = self.module_dictionary[m_id]
            module.active_w_type = active_w_type
            module.up = connections[0]
            module.right = connections[1]
            module.down = connections[2]
            module.left = connections[3]
            booleans = list(map(bool, map(int, booleans)))
            module.shadowed = booleans[0]
            module.is_start = booleans[1]
            module.is_end = booleans[2]

            self.current_modules.append(module)

        self.free_modules = [m for m in self.all_modules if m not in self.current_modules]

        main_line = []
        if S[2]:
            for m_id in S[2].split(','):
                main_line.append(self.module_dictionary[m_id])

        self.main_line = main_line

    def update_active_works(self, worked):
        for m in self.main_line:
            pass


    def modules_in_config(self, configuration_str):
        """ Creates a list of modules that are in the configuration string.
        :param Configuration_str: A string representing a configuration, retrived by the configuration_str method
        :return: A list of modules that are in configuration_str
        """
        if not isinstance(configuration_str, str):
            raise ValueError("configuration_str should be a string!")
        result = []
        S = configuration_str.split(sep='|')
        M = S[1].split(sep=':')
        for ms in M:
            m_id = re.search('(.*)(?=\{)', ms).group(0)  #
            result.append(self.module_dictionary[m_id])

        return result

    def modules_not_in_config(self, configuration_str):
        """ The inverse of modules_in_config
        :param configuration_str: A string representing a configuration, retrived by the configuration_str method
        :return: All modules that are not in the configuration_str
        """
        in_str = self.modules_in_config(configuration_str)
        return [m for m in self.module_dictionary.values() if m not in in_str]

    def reset_modules(self):
        for m in self.all_modules:
            m.up = None
            m.right = None
            m.down = None
            m.left = None
            m.active_w_type = set()

    def make_grid(self, mod):
        if self.current_modules:
            return mod.make_grid()
        else:
            return {}


    def grid_conflicts(self):

        def invert_dict(d):
            res = {}
            for k in d:
                res.setdefault(d[k], set()).add(k)
            return res

        grid = self.make_grid()
        inverted_grid = invert_dict(grid)
        conflicts = {k: v for k, v in inverted_grid.items() if len(v) > 1}
        return conflicts

    def take_transport_module(self):
        if self.free_transporters:
            t = self.free_transporters[0]
            self.free_transporters.remove(t)
        else:
            t = deepcopy(self.transport_module)
            t.m_id = "transporter" + str(self.transport_id)
            self.module_dictionary[t.m_id] = t
            self.transport_id += 1
        self.transport_modules.append(t)
        self.all_modules.append(t)
        # self.current_modules.append(t)  #TODO: Adder også til current_modules. Find hvorfor.

        return t

    def free_transport_module(self, t):
        if t in self.current_modules:
            self.current_modules.remove(t)
        t.total_wipe()
        self.free_transporters.append(t)

    def set_active_work(self, worked):
        for m, works in worked.items():
            if m in self.current_modules:
                m.active_w_type = set(works)

    def find_lines(self):
        main_line = self.main_line

        lines = []
        for mod in self.current_modules:
            mod_in_line = False
            for l in lines:
                if mod in l:
                    mod_in_line = True
            if not mod_in_line:
                all_left = mod.traverse_in_left()
                all_left.remove(all_left[-1])
                all_right = mod.traverse_right()
                lines.append(all_left + all_right)

        up_lines = []
        down_lines = []
        grid = self.make_grid(main_line[0])
        for l in lines:
            if l is not main_line:
                if grid[l[0]][1] > 0:
                    up_lines.append(l)
                else:
                    down_lines.append(l)

        return main_line, up_lines, down_lines

    def swap_modules(self, m0, m1):
        u0 = m0.up
        r0 = m0.right
        d0 = m0.down
        l0 = m0.left
        iu0 = m0.in_up
        ir0 = m0.in_right
        id0 = m0.in_down
        il0 = m0.in_left

        active0 = m0.active_w_type

        m0.up = m1.up
        m0.right = m1.right
        m0.down = m1.down
        m0.left = m1.left
        if m1.in_up:
            m1.in_up.down = m0
        if m1.in_right:
            m1.in_right.left = m0
        if m1.in_down:
            m1.in_down.up = m0
        if m1.in_left:
            m1.in_left.right = m0

        m0.active_w_type = m1.active_w_type

        m1.up = u0
        m1.right = r0
        m1.down = d0
        m1.left = l0
        if iu0:
            iu0.down = m1
        if ir0:
            ir0.left = m1
        if id0:
            id0.up = m1
        if il0:
            il0.right = m1
        m1.active_w_type = active0

        if m0 in self.current_modules and m1 in self.free_modules:
            self.current_modules.remove(m0)
            self.free_modules.append(m0)
            self.free_modules.remove(m1)
            self.current_modules.append(m1)
        elif m1 in self.current_modules and m0 in self.free_modules:
            self.current_modules.remove(m1)
            self.free_modules.append(m1)
            self.free_modules.remove(m0)
            self.current_modules.append(m0)

        for r in self.recipes:
            if r.start_module == m0:
                r.start_module = m1
            elif r.start_module == m1:
                r.start_module = m0

        temp0 = [0 if m == m0 else m for m in self.main_line]
        temp1 = [m0 if m == m1 else m for m in temp0]
        temp2 = [m1 if m == 0 else m for m in temp1]
        self.main_line = temp2
