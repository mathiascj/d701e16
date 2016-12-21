import networkx as nx
import matplotlib.pyplot as plt

class Recipe:
    def __init__(self, name, dependencies, start_module, start_direction, amount):
        """

        :param dependencies: Dictionary representing dependency graph
        :param start_module: Initial module for production
        :param start_direction: Origin point into start module
        """
        self.name = str(name)
        self.dependencies = dependencies
        self.start_module = start_module
        self.start_direction = start_direction
        self.amount = amount

    def __getitem__(self, item):
        return self.dependencies[item]

    def values(self):
        """
        :return: Nodes that depend on others
        """
        return self.dependencies.values()

    def keys(self):
        """
        :return: All nodes
        """
        return self.dependencies.keys()

    def items(self):
        """
        :return: All parent/child pairs
        """
        return self.dependencies.items()

    def __len__(self):
        """
        :return: Number of nodes
        """
        return len(self.dependencies)

    def to_DiGraph(self):
        """
        Transforms creates a directed graph from dependencies
        :return:  A directed graph
        """
        G = nx.DiGraph()

        # Gets nodes
        nodes = {item for sublist in self.values() for item in sublist}
        nodes |= set(self.keys())
        G.add_nodes_from(nodes)

        # Gets edges
        for item in self.items():
            for dependency in item[1]:
                G.add_edge(item[0], dependency)
        return G

    def list_to_Digraph(self, L):
        G = nx.DiGraph()
        G.add_nodes_from(L)
        for i, node in enumerate(L):
            if (i != len(L) - 1):
                G.add_edge(L[i+1], node)

        return G

    def to_topological_sorted_DiGraph(self):
        """
        From dependencies constructs a directed graph, which is topologically sorted
        :return:  Topologically sorted graph
        """
        return self.list_to_Digraph(nx.topological_sort(self.to_DiGraph()))

    def recipe_str(self):
        return self.name + "@" + self.start_module + "&" + str(self.start_direction)

    @staticmethod
    def get_flow_graph(recipes):
        """
        Combines several recipes into a single graph
        :param recipes: a list of dicts
        :return: Combined directed graph
        """
        G = nx.DiGraph()

        # Topologically sort all recipes
        sorted_recipes = []
        for r in recipes:
            sr = r.to_topological_sorted_DiGraph()
            sorted_recipes.append(sr)

        # Compose together the sorted recipes into G
        for r in sorted_recipes:
            G.add_nodes_from(r)
            G = nx.compose(G, r)

        return G


    # @staticmethod
    # def kahn_topological_sort(graph, start_node):
    #     """
    #     Topologically sorts a directed graph
    #     :param graph: Graph to be sorted
    #     :param start_node: Node from where sort should start
    #     :return: A sorted graph
    #     """
    #     L = []
    #
    #     # Get all nodes that do not depend on anyone else
    #     S = {n for n in graph.nodes() if not graph.successors(n)}
    #     first = True
    #
    #     # Creates a toplocially sorted sequence of nodes
    #     while S:
    #         # Makes sure we pop start_node first
    #         if first:
    #             n = start_node
    #             S.remove(n)
    #             first = False
    #         else:
    #             n = S.pop()
    #         # Append popped node to sequence, then add any freed up nodes to S
    #         L += [n]
    #         for m in [m for m, x in graph.edges() if x == n]:
    #             graph.remove_edge(m, n)
    #             if not graph.successors(m):
    #                 S.add(m)
    #
    #     # If not all edges have been removed, we have a cycle
    #     x = graph.edges()
    #     if x:
    #         raise ValueError('Graph has at least one cycle')
    #     else:
    #         # From the sequence of nodes in L, creates a graph
    #         G = nx.DiGraph()
    #         G.add_nodes_from(L)
    #         for i in range(1, len(L)):
    #             G.add_edge(L[i], L[i - 1])
    #         return G

    @staticmethod
    def plot(G):
        """
        Plots a graph
        :param G: Graph to be plotted
        """
        pos1 = nx.layout.spring_layout(G, iterations=50)
        nx.draw(G, pos=pos1)
        nx.draw_networkx_labels(G, pos=pos1)
        plt.show()


