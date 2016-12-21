from xml.etree.ElementTree import parse

# GLOBALS DECLS
# String decls put here for the sake of easier reconfiguration
STR_NUMBER_OF_MODULES = "NUMBER_OF_MODULES"
STR_NUMBER_OF_RECIPES = "NUMBER_OF_RECIPES"
STR_NUMBER_OF_WORKTYPES = "NUMBER_OF_WORKTYPES"
STR_NUMBER_OF_OUTPUTS = "NUMBER_OF_OUTPUTS"
STR_NUMBER_OF_INITS = "NUMBER_OF_INITS"

STR_MID = "mid"  # Module ID
STR_RID = "rid"  # Recipe ID
STR_WID = "wid"  # Worktype ID
STR_DID = "did"  # Direction ID

STR_NODE = """
typedef struct {
	wid_t work;
	int number_of_parents;
	int children[NUMBER_OF_WORKTYPES];
	int number_of_children;
} node;"""

STR_WA = "work_array"
STR_PA = "ptime_array"
STR_CA = "crate_array"
STR_NA = "next_array"
STR_TA = "ttime_array"

STR_MODULE_QUEUE = "mqueue"
STR_MODULE_WORKER = "mworker"
STR_MODULE_TRANSPORTER = "mtransporter"

STR_RECIPE_NAME = "recipe"


def const_int_decl(variable_name, init_value):
    """
    :param variable_name: Name of the variable
    :param init_value: Value that the variable be instantiated to
    :return: A const int declaration
    """
    return "const " + int_decl(variable_name, init_value)


def int_decl(variable_name, init_value=""):
    """
    :param variable_name: Name of the variable
    :param init_value: Value that the variable be instantiated to
    :return: An int declaration
    """
    s = "int " + variable_name
    if init_value:
        s += " = " + str(init_value)
    s += ";\n"
    return s


def typedef_decl(type_name, max_val):
    """
    :param type_name: The name of the new type, will be appended with _t and _safe_t
    :param max_val: The maximum value of the new type minus one
    :return: A string declaring a two types, an unsafe and a safe one.
    """
    s = "typedef int[-1, " + str(max_val) + " - 1] " + type_name + "_t;\n"
    s += "typedef int[0, " + str(max_val) + " - 1] " + type_name + "_safe_t;\n"
    return s


def chan_decl(chan_name, size="", urgent=False):
    """
    :param chan_name: Name of the channel
    :param size: Size of the channel
    :param urgent: Bool if the channel should be urgent
    :return: A string that declare the channel
    """
    s = ""
    if urgent:
        s += "urgent "

    if size:
        size_string = "[" + str(size) + "]"
    else:
        size_string = ""

    return s + "chan " + chan_name + size_string + ";\n"


def create_model_xml(file, global_decl_string, system_string, new_file):
    """
    Updates base UPPAAL xml file using input strings as replacement
    :param file: Path to base file
    :param global_decl_string: String to replace global declaration
    :param recipe_strings: String to create new recipe templates
    :param system_string: String to replace system
    :param new_file: Path to new file
    """
    tree = parse(file)

    # Overwrite text in the global declaration
    global_decl = tree.find("declaration")
    global_decl.text = global_decl_string

    # Remove system node
    system_decl = tree.find("system")
    system_decl.text = system_string

    tree.write(new_file)


def generate_xml(template_file, modules, recipes, xml_name="test.xml", q_name="test.q"):
    """
    Method to be called directly by user.
    Based on modules and recipes a new UPPAAL model is formed.
    :param template_file: Path to base UPPAAL file of the model
    :param modules: A list of FESTO modules
    :param recipes: A list of recipes, each being a functional dependency graph
    :param new_file_name: Path to new file
    """

    # Module id mapping
    m_id = 0
    m_id_dict = {}
    for module in modules:
        m_id_dict[module.m_id] = m_id
        m_id += 1

    inverted_m_id_dict = {v: k for k, v in m_id_dict.items()}

    # Finds number of unique worktypes that can be performed with the modules
    S = set()

    for m in modules:
        S.update(m.w_type)
    number_of_worktypes = len(S)

    # Work id mapping
    w_id = 0
    w_id_dict = {}
    for w in S:
        w_id_dict[w] = w_id
        w_id += 1

    inverted_w_id_dict = {v: k for k, v in w_id_dict.items()}

    # Generation of global string
    number_of_recipes = sum([x.amount for x in recipes])
    global_decl_string = generate_global_declarations(len(modules), number_of_recipes, number_of_worktypes, 4)

    # Generation of system string
    system_string, recipe_names, r_id_dict\
        = generate_system_declaration(modules, number_of_worktypes, recipes, m_id_dict, w_id_dict)

    # Write xml and query files
    create_model_xml(template_file, global_decl_string, system_string, xml_name)
    create_query(recipe_names, q_name)

    return inverted_m_id_dict, inverted_w_id_dict, r_id_dict


def generate_global_declarations(number_of_modules, number_of_recipes, number_of_worktypes, number_of_outputs=4):
    """
    Generates a string to replace text in global declaration node
    :param number_of_modules: Number of modules in model
    :param number_of_worktypes: Number of unique work types
    :param number_of_recipes: Number of recipes
    :return global declaration string
    """
    s = "// Global Declarations\n"

    # Constants
    s += "// Constants\n"
    s += const_int_decl(STR_NUMBER_OF_MODULES, number_of_modules)
    s += const_int_decl(STR_NUMBER_OF_RECIPES, number_of_recipes)
    s += const_int_decl(STR_NUMBER_OF_WORKTYPES, number_of_worktypes)
    s += const_int_decl(STR_NUMBER_OF_OUTPUTS, number_of_outputs)
    s += const_int_decl(STR_NUMBER_OF_INITS, (number_of_modules * 3) + 2)
    s += "\n"

    # Types
    s += "// User defined types.\n"
    s += "// Safe means that we cannot go to -1.\n"
    s += "// -1 is however sometimes needed as a filler value, so it can be permitted.\n"
    s += typedef_decl(STR_MID, STR_NUMBER_OF_MODULES)
    s += typedef_decl(STR_RID, STR_NUMBER_OF_RECIPES)
    s += typedef_decl(STR_WID, STR_NUMBER_OF_WORKTYPES)
    s += typedef_decl(STR_DID, STR_NUMBER_OF_OUTPUTS)
    s += "\n"

    # Structs
    s += STR_NODE
    s += "\n"

    # Channels
    s += "// Channels\n"
    s += chan_decl("enqueue", STR_NUMBER_OF_MODULES, True)
    s += chan_decl("work_dequeue", STR_NUMBER_OF_MODULES)
    s += chan_decl("transport_dequeue", STR_NUMBER_OF_MODULES)
    s += chan_decl("intern", STR_NUMBER_OF_MODULES, True)
    s += chan_decl("remove", STR_NUMBER_OF_RECIPES)
    s += chan_decl("rstart", STR_NUMBER_OF_RECIPES)
    s += chan_decl("handshake", STR_NUMBER_OF_RECIPES)
    s += chan_decl("work", STR_NUMBER_OF_WORKTYPES)
    s += chan_decl("initialize", STR_NUMBER_OF_INITS)
    s += chan_decl("urg", "", True)
    s += "chan priority transport_dequeue < work_dequeue" \
         " < intern < handshake < work < enqueue < default < rstart < remove < urg;"
    s += "\n"

    # Clock
    s += "// Global clock\n"
    s += "clock global_c;\n"
    s += "\n"

    # Global functions and their variables
    s += """
//Variables used for passing values at handshake
int var = -1;
int var2 = -1;
bool can_continue = true;
bool can_add_recipe = true;

//Functions for tracking completed recipes
bool ra_done[NUMBER_OF_RECIPES];

void init_ra_done(){
    int i;
    for(i = 0; i < NUMBER_OF_RECIPES; ++i)
        ra_done[i] = false;
}

bool is_done(rid_safe_t rid){
    return ra_done[rid];
}


bool current_works[NUMBER_OF_RECIPES][NUMBER_OF_WORKTYPES];

void init_current_works(){
    int i, j;
    for(i = 0; i < NUMBER_OF_RECIPES; ++i)
        for(j = 0; j < NUMBER_OF_WORKTYPES; ++j)
            current_works[i][j] = false;
}


bool can_work(bool worktype[NUMBER_OF_WORKTYPES], rid_safe_t rid){
    int i;
    for(i = 0; i < NUMBER_OF_WORKTYPES; ++i){
        if(worktype[i] &&  current_works[rid][i])
            return true;}
    return false;
}

bool full_modules[NUMBER_OF_MODULES];
bool idle_workers[NUMBER_OF_MODULES];
bool idle_transporters[NUMBER_OF_MODULES];
"""
    return s


def generate_system_declaration(modules, number_of_worktypes, recipes, m_id_dict, w_id_dict):
    """
    Generates system declaration
    :param modules: module objects
    :param number_of_worktypes: number of unique types of work
    :param recipes: recipe object
    :return: system declaration string and recipe names
    """
    init_index = 0
    s = ""

    # Declaring modules
    system_list = []
    for m in modules:
        decl_string, queue_name, worker_name, transporter_name, i = \
            generate_module_declaration(m, number_of_worktypes, 4, init_index, m_id_dict, w_id_dict)
        s += decl_string
        system_list.append(queue_name)
        system_list.append(worker_name)
        system_list.append(transporter_name)
        init_index = i

    # Declaring recipes
    recipe_names = []
    recipe_counter = 0

    r_id_dict = {}
    for r in recipes:
        decl_string, names, dic =\
            generate_recipe_declaration(recipe_counter, r, number_of_worktypes, m_id_dict, w_id_dict)
        recipe_names = recipe_names + names
        recipe_counter += r.amount
        s += decl_string
        r_id_dict.update(dic)


    # Declaring recipe queue
    s += "rid_t rqa[" + STR_NUMBER_OF_RECIPES + "]" + " = {"
    s += ",".join([str(x) for x in range(recipe_counter)])
    s += "};\n"

    s += "rqueue = RecipeQueue(rqa, " + str(init_index) + ");"
    system_list.append("rqueue")
    init_index += 1

    # Declaring remover
    s += "rem = Remover(" + str(init_index) + ");\n"
    system_list.append("rem")
    init_index += 1

    # Declaring Initializer
    s += "initer = Initializer();\n"
    system_list.append("initer")

    # Declaring Urgent
    s += "urge = Urgent();\n"
    system_list.append("urge")

    # Declaring system instance
    s += generate_system_instance(system_list + recipe_names)

    return s, recipe_names, r_id_dict


def generate_module_declaration(module, number_of_worktypes, number_of_outputs, init_index, m_id_dict, w_id_dict):
    """
    Creates a declration for a module
    :param module: Module object
    :param number_of_worktypes: Total number of worktypes across recipe
    :param number_of_outputs: Number of output directions for modules
    :return: strings declaring module
    """

    # Getting the mapped id
    m_id = m_id_dict[module.m_id]

    # Setting up arrays
    s = "// Module " + str(m_id) + "\n"
    wa, temp = work_array(module, number_of_worktypes, m_id, w_id_dict)
    s += temp
    pa, temp = p_time_array(module, number_of_worktypes, m_id, w_id_dict)
    s += temp
    na, temp = next_array(module, number_of_outputs, m_id, m_id_dict)
    s += temp
    ta, temp = t_time_array(module, number_of_outputs, m_id)
    s += temp

    # Instantiates module queue template
    module_queue = STR_MODULE_QUEUE + str(m_id)
    s += module_queue + " = ModuleQueue(" \
         + str(m_id) + ", " \
         + str(init_index) + ", " \
         + str(module.queue_length) + ", " \
         + wa + ", " \
         + str(module.allow_passthrough).lower() \
         + ");\n"
    init_index += 1

    # Instantiates module worker template
    module_worker = STR_MODULE_WORKER + str(m_id)
    s += module_worker + " = ModuleWorker(" \
         + str(m_id) + ", " \
         + str(init_index) + ", " \
         + wa + ", " \
         + pa \
         + ");\n"
    init_index += 1

    # Instantiates module transporter template
    module_transporter = STR_MODULE_TRANSPORTER + str(m_id)
    s += module_transporter + " = ModuleTransporter(" \
         + str(m_id) + ", " \
         + str(init_index) + ", " \
         + ta + ", " \
         + na + ", " + str(module.allow_passthrough).lower() \
         + ");\n\n"
    init_index += 1

    return s, module_queue, module_worker, module_transporter, init_index


def work_array(module, number_of_worktypes, m_id, w_id_dict):
    """
    :param module:  Module for which we create a work array
    :param number_of_worktypes: Amount of unique work types total
    :return: The name of the var and a string of code that declares the var
    """

    varname = STR_WA + str(m_id)  # array name
    w_ids = [w_id_dict[id] for id in module.w_type]  # mapped work ids

    s = "const bool " + varname + "[" + STR_NUMBER_OF_WORKTYPES + "] = {"
    s += ",".join(["true" if x in w_ids
                   else "false" for x in range(number_of_worktypes)])
    s += "};\n"

    return varname, s


def p_time_array(module, number_of_worktypes, m_id, w_id_dict):
    """
    :param module: Module object
    :param number_of_worktypes: total number of work types across recipe
    :return: string instantiating p_time array.
    """
    varname = STR_PA + str(m_id)
    w_ids = [w_id_dict[id] for id in module.w_type]  # mapped work ids
    inverted_w_id_dict = {v: k for k, v in w_id_dict.items()}

    s = "const int " + varname + "[" + STR_NUMBER_OF_WORKTYPES + "] = {"
    s += ",".join([str(module.p_time[inverted_w_id_dict[x]]) if x in w_ids
                   else "0" for x in range(number_of_worktypes)])
    s += "};\n"

    return varname, s


def next_array(module, number_of_outputs, m_id, m_id_dict):
    """
    :param module: Module object
    :param number_of_outputs: Number of neighbours a module can have
    :return: string of array describing module's neighbours
    """
    varname = STR_NA + str(m_id)

    s = "const mid_t " + varname + "[" + STR_NUMBER_OF_OUTPUTS + "] = {"
    s += ",".join([str(m_id_dict[module.connections[x].m_id]) if module.connections[x]
                   else "-1" for x in range(number_of_outputs)])
    s += "};\n"
    return varname, s


def t_time_array(module, number_of_outputs, m_id):
    """
    :param module: Module object
    :param number_of_outputs: Number of total work types across recipe
    :return: string instantiating t_time array
    """
    varname = STR_TA + str(m_id)

    # Find traveling times when entering from each direction
    sub_arrays = []
    for i in range(number_of_outputs):
        sub_array = []
        for j in range(number_of_outputs):
            sub_array.append(str(module.t_time[i][j]))
        sub_arrays.append("{" + ",".join(sub_array) + "}")

    s = "const int " + varname + "[" + STR_NUMBER_OF_OUTPUTS + "][" + STR_NUMBER_OF_OUTPUTS + "] = {"
    s += ",".join(sub_arrays)
    s += "};\n"
    return varname, s


def generate_recipe_declaration(counter, recipe, number_of_worktypes, m_id_dict, w_id_dict):
    """
    Generates the part of system that declares new recipes
    :param id: ID of recipe
    :param recipe: a functional dependency graph
    :return: string to declare a recipe in system
    """

    size = STR_NUMBER_OF_WORKTYPES
    node_strings, number_of_nodes = generate_nodes(recipe, number_of_worktypes, w_id_dict)

    s = "// Recipe " + recipe.name + "\n"

    # Creates all recipe nodes
    node_names = []
    for index, node in enumerate(node_strings):
        name = "r" + recipe.name + "node" + str(index)
        node_names.append(name)
        s += "const node " + name + " = " + str(node) + "; \n"

    # Puts nodes into list
    func_dep_string = "func_dep" + recipe.name
    s += "node " + func_dep_string + "[" + size + "] = {" + ",".join(node_names) + "}; \n"

    # Declares number of nodes
    number_of_nodes_string = "number_of_nodes" + recipe.name
    s += "const int " + number_of_nodes_string + " = " + str(number_of_nodes) + "; \n"

    # Instantiates recipe templates
    recipe_names = []
    r_id_dict = {}
    for x in range(recipe.amount):
        r_id = str(x + counter)
        recipe_name = "recipe" + r_id
        recipe_names.append(recipe_name)
        s += recipe_name + " = Recipe(" + r_id + ", " + str(m_id_dict[recipe.start_module]) + \
             ", " + func_dep_string + ", " + number_of_nodes_string + ", " + str(recipe.start_direction) + ");\n\n"

        r_id_dict[x + counter] = recipe.name


    return s, recipe_names, r_id_dict


def generate_nodes(recipe, number_of_worktypes, w_id_dict):
    nodes = []
    child_mapping = {-1: -1}

    # For each node add information to the initialization lists
    for index, entry in enumerate(recipe.items()):
        node = {}
        work = entry[0]
        deps = entry[1]

        node['work'] = work
        node['number_of_parents'] = len(deps)

        # Gets children of node
        children = []
        for node_id, parents in recipe.items():
            if work in parents:
                mapped_id = w_id_dict[node_id]
                children.append(mapped_id)

        node['number_of_children'] = len(children)

        # Fills out rest of children list with -1s
        while len(children) < number_of_worktypes:
            children.append(-1)

        node['children'] = children

        # Creates a mapping between the node's work and its index in the final list of nodes.
        child_mapping[w_id_dict[work]] = index

        nodes.append(node)

    node_strings = []
    for node in nodes:
        # Maps the old children values to ones based on the child's index in the final list of nodes.
        node['children'] = [child_mapping[x] for x in node['children']]

        # Creates a string, delcaring the given node and stores it.
        children_string = ("{" + ", ".join(map(str, node['children'])) + "}")
        node_string = "{" + str(w_id_dict[node['work']]) + ", " + str(node['number_of_parents']) + \
                      ", " + children_string + ", " + str(node['number_of_children']) + "}"
        node_strings.append(node_string)

    number_of_nodes = len(node_strings)

    # Fills up remaining array with empty nodes
    while len(node_strings) < number_of_worktypes:
        node_strings.append(generate_empty_node(number_of_worktypes))

    return node_strings, number_of_nodes


def generate_empty_node(number_of_worktypes):
    """
    Creates an empty nodes for recipe declaration.
    :param number_of_worktypes: total number of worktypes across recipes
    :return: string to instantiate an empty node
    """
    children = [-1 for x in range(number_of_worktypes)]
    return "{ -1, -1, {" + ",".join(map(str, children)) + "}, -1}"


def generate_system_instance(system_list):
    """
    To system declaration, generates a string including all modules and recipes
    :param number_of_modules: total number of FESTO modules
    :param number_of_recipes: total number of recipes
    :return: string to add all recipes and modules to system
    """
    s = "system "
    s += "< ".join(system_list)
    s += ";"
    return s


def create_query(recipe_names, q_name="test.q"):
    """
    Generates a query file, containing a query to check whether all recipes are done.
    :param recipe_names: Names of the recipes for which a query will be generated
    :param new_file_name: path to new file
    """
    s = "E<> "
    for i, recipe in enumerate(recipe_names):
        s += recipe + ".done"
        if i != len(recipe_names) - 1:
            s += " and "
    f = open(q_name, 'w')
    f.write(s)
    f.close()
