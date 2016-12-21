from networkx import nx
from random import shuffle

def get_top_nodes(G):
    """
    Finds all nodes with no successors
    :param G: a nx Digraph
    :return: a list of tuples, each tuple containing node name and node attribute dict
    """
    top_nodes = []
    for node in G.nodes(data=True):
        if not G.successors(node[0]):
            top_nodes.append(node)

    return top_nodes


# THIS IS THE POLICE SPEAKING
# THIS IS A GENERATOR NOT A FUNCTION, BE WARY CITIZEN
def initial_configurations(G, modules, csh, setup, recipe_starters, active_works):
    """
    If possible creates a linear configuration.
    :param G: Graph describing recipes
    :param modules: modules which may be placed
    :param setup:  linear configuration setup up till now
    :param recipe_starters: dict describing which module each recipe starts at
    :param active_works: dict describing what works a module performs
    :param branches: A list, where each element is a list of arguments,
           which called on this function lets us explore a new branch
    :return:  Empty list if no branches are left

    """

    # Creates copies to get around referential integrity :-)
    G_copy = G.copy()
    recipe_starters_copy = recipe_starters.copy()
    active_works_copy = active_works.copy()

    # If a setup is already given, remove as many top nodes as possible
    top_nodes = []
    if setup:
        flag = True  # Flag tells if we may remove more top nodes
        while flag:
            flag = False
            current_module = setup[-1]
            top_nodes = get_top_nodes(G_copy)
            for node in top_nodes:
                work = node[0]
                starts = node[1]['starts']

                #  If the top node is workable by the current module it is removed
                if work in current_module.w_type:
                    flag = True
                    G_copy.remove_node(work)

                    # Updates recipe_starters dict, if a recipe should start at current_module
                    for start in starts:
                        if start not in recipe_starters_copy:
                            recipe_starters_copy[start] = current_module

                    # Updates active_works for current module with the removed top node
                    if current_module not in active_works_copy:
                        active_works_copy[current_module] = set()
                    active_works_copy[current_module].add(work)

    # If setup is empty just get the top nodes
    else:
        top_nodes = get_top_nodes(G_copy)

    new_branches = []

    # If graph is empty we yield the setup
    if not G_copy:
        csh.reset_modules()

        # Constructs setup
        for i,m in enumerate(setup):
            if(i + 1 < len(setup)):
                m.right = setup[i + 1]
            # Sets active works in module
            m.active_w_type = active_works_copy[m]

        # Sets start module of recipes
        for r in csh.recipes:
            r.start_module = recipe_starters_copy[r.name].m_id

        csh.current_modules = setup
        csh.main_line = setup

        yield csh.configuration_str()

    # If graph is not empty we try placing new modules.
    else:
        for node in top_nodes:
            work = node[0]
            mods = [m for m in modules if work in m.w_type]
            shuffle(mods) # Makes sure we yield random branches
            # Places down a module and constructs a new branch from this choice
            for m in mods:
                update_mods = modules.copy()
                update_mods.remove(m)
                new_setup = setup + [m]
                yield from initial_configurations(G_copy, update_mods, csh, new_setup, recipe_starters_copy, active_works_copy)



def recipes_to_graph(recipes):
    """
    Given a list of recipes, will create a func dep graph for each which it will then compose.
    :param recipes: A list of recipe object
    :return: A combined graph where the 'starts' attribute for each node has been set
    """
    result_graph = nx.DiGraph()

    for r in recipes:
        # Turn recipe to graph and get top nodes
        r_graph = r.to_DiGraph()
        top_nodes = get_top_nodes(r_graph)
        top_nodes = [x[0] for x in top_nodes]  # Get only names of nodes not attributes

        # Iterate over each node in graph
        for node in r_graph.nodes(data = True):
            work = node[0]
            attributes = node[1]

            # If node is a top node, it has its starts attribute set to the recipe name
            attributes['starts'] = set()
            if work in top_nodes:
                attributes['starts'].add(r.name)

                # If this node is already in the result_graph we store elements from its start attributes
                # in the r_graph node, as to retain it after compose.
                if work in result_graph:
                    res_set = result_graph.node[work]['starts']
                    attributes['starts'].update(res_set)

        # Attributes of r_graph take presedence over result_graph's
        result_graph = nx.compose(result_graph, r_graph)
    return result_graph


def initial_configuration_generator(recipes, modules, csh):
    G = recipes_to_graph(recipes)
    return initial_configurations(G, modules, csh, [], {}, {})