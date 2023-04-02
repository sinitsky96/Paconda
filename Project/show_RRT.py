import networkx as nx
import matplotlib.pyplot as plt
with open("rrt_tree_for_ghost_1.txt") as f:
    G=nx.Graph()
    for line in f.read().splitlines():
        print(len(line))
        trre=eval(line)
        print(trre)
        points =[tuple(x[0]) for x in trre]
        edges = [tuple((tuple(x[0]),points[x[1]])) for x in trre]
        for i,node in enumerate(points):
            G.add_node(node,x=node[0],y=node[1])
        for i,edge in enumerate(edges):
            G.add_edge(*edge)
    pos = {node: (G.nodes[node]['x'], G.nodes[node]['y']) for node in G.nodes()}
    nx.draw(G, pos, with_labels=False, node_size=1, node_color='r', width=0.5, alpha=0.5, edge_color='b')
    plt.show()