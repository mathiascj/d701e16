from UPPAAL.verifytaAPI import run_verifyta, trace_time, property_satisfied, pprint
from UPPAAL.xml_generator import generate_xml
import re

XML_FILE = 'temp.xml'
Q_FILE = 'temp.q'

VERIFYTA = '../UPPAAL/verifyta'
XML_TEMPLATE = "../../Modeler/iter3.4.2.xml"

def get_best_time(recipes, modules, template_file=XML_TEMPLATE, verifyta=VERIFYTA):
    """
    Gets the best cost of a given configuration, modules and recipes
    :param configuration: A configuraion of modules
    :param modules: A list of modules
    :param recipes: A list of recipes
    :param template_file: A path to a template UPPAAL CORA XML file
    :param verifyta: A path to an instance of UPPAAL CORAs verifyta
    :return: The best cost of the configuration
    """
    m_map, w_map, r_map =\
        generate_xml(template_file=template_file, modules=modules.copy(), recipes=recipes.copy(), xml_name=XML_FILE, q_name=Q_FILE)

    result, trace = run_verifyta(XML_FILE, Q_FILE, "-t 2", "-o 3", "-u", "-y", verifyta=verifyta)

    if property_satisfied(result):
        time = trace_time(trace)
        trace_iter = iter((trace.decode('utf-8')).splitlines())
        worked_on, transported_through, active_works = get_travsersal_info(trace_iter, m_map, r_map, w_map)

        return time, worked_on, transported_through, active_works
    else:
        raise RuntimeError("Could not verify the properties, see the temp files")



def get_travsersal_info(trace_iter, module_map, recipe_map, work_map):
    """
    :param trace_iter: An iterator to run over lines in trace output
    :param module_map: A mapping from UPPAAL m_ids to the originals
    :param recipe_map: A mapping from UPPAAL r_ids to the originals
    :return: worked on: dict telling us for each module, what recipe types have been worked by it
             transported_through: dict telling us for each module, what recipe types have been transorted through it.
    """

    worked_on = {}
    transported_through = {}
    active_works = {}

    for line in trace_iter:
        if line == "Transitions:":
                lines = []
                counter = 0

                # Get the two lines describing the transition
                for line in trace_iter:
                    lines.append(line)
                    counter += 1
                    if counter == 2:
                        break

                # If the transition is a handshake. Work is being performed.
                if "handshake" in lines[0]:
                    r_id = int(re.findall("\d+", lines[0])[0])

                    m_id = int(re.findall("\d+", lines[1])[0])
                    m_id = module_map[m_id]

                    if m_id not in worked_on:
                        worked_on[m_id] = set()

                    # Adds recipe type to the given module
                    worked_on[m_id].add((recipe_map[r_id]))

                if "work" in lines[0] and 'Handshaking' in lines[0]:
                    m_id = int(re.findall("\d+", lines[0])[0])
                    m_id = module_map[m_id]

                    w_id = int(re.findall('\[(.*?)\]', lines[1])[0])
                    w_id = work_map[w_id]

                    if m_id not in active_works:
                        active_works[m_id] = set()

                    active_works[m_id].add(w_id)

                # If the transition is an enqueue using a transporter. Transportation is being performed.
                elif "enqueue" in lines[0] and "mtransporter" in lines[0]:
                    m_id = int(re.findall("\d+", lines[0])[0])
                    m_id = module_map[m_id]

                    # Gets the line describing the state after transition
                    state_line = ""
                    counter = 0
                    for line in trace_iter:
                        counter += 1
                        if counter == 5:
                            state_line = line
                            break

                    # Gets the id of the recipe, lying in the global var
                    r_id = int(re.findall("var=(\d+)", state_line)[0])

                    if m_id not in transported_through:
                        transported_through[m_id] = set()

                    # Adds recipe type to the given module
                    transported_through[m_id].add(recipe_map[r_id])

    return worked_on, transported_through, active_works