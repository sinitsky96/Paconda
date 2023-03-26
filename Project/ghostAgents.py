# ghostAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.

# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from game import Agent
from game import Actions
from game import Directions
import random
from util import manhattanDistance, bresenham
import util
import numpy as np

class GhostAgent(Agent):
    def __init__(self, index, state=None):
        self.index = index

    def getAction(self, state):
        dist = self.getDistribution(state)
        if len(dist) == 0:
            return Directions.STOP
        else:
            return util.chooseFromDistribution(dist)

    def getDistribution(self, state):
        "Returns a Counter encoding a distribution over actions from the provided state."
        util.raiseNotDefined()


class RandomGhost(GhostAgent):
    "A ghost that chooses a legal action uniformly at random."

    def getDistribution(self, state):
        dist = util.Counter()
        for a in state.getLegalActions(self.index): dist[a] = 1.0
        dist.normalize()
        return dist


class DirectionalGhost(GhostAgent):
    "A ghost that prefers to rush Pacman, or flee when scared."

    def __init__(self, index, state=None, prob_attack=0.8, prob_scaredFlee=0.8):
        print("diractionl ghost Index: ", index)
        self.index = index
        self.prob_attack = prob_attack
        self.prob_scaredFlee = prob_scaredFlee

    def getDistribution(self, state):
        # Read variables from state
        ghostState = state.getGhostState(self.index)
        legalActions = state.getLegalActions(self.index)
        pos = state.getGhostPosition(self.index)
        isScared = ghostState.scaredTimer > 0
        speed_rnd = lambda: random.uniform(0.2, 1.0)
        speed = speed_rnd()
        if isScared: speed = speed_rnd() * 0.5
        actionVectors = [Actions.directionToVector(a, speed) for a in legalActions]
        newPositions = [(pos[0] + a[0], pos[1] + a[1]) for a in actionVectors]
        pacmanPosition = state.getPacmanPosition()

        # Select best actions given the state
        distancesToPacman = [manhattanDistance(pos, pacmanPosition) for pos in newPositions]
        if isScared:
            bestScore = max(distancesToPacman)
            bestProb = self.prob_scaredFlee
        else:
            bestScore = min(distancesToPacman)
            bestProb = self.prob_attack
        bestActions = [action for action, distance in zip(legalActions, distancesToPacman) if distance == bestScore]

        # Construct distribution
        dist = util.Counter()
        for a in bestActions: dist[a] = bestProb / len(bestActions)
        for a in legalActions: dist[a] += (1 - bestProb) / len(legalActions)
        dist.normalize()
        return dist


##### PRM ghost #####
from My_PRM import Roadmap
from math import ceil, floor


class PRMGhost(GhostAgent):
    """
    A ghost that only know the world via PRM    """

    def __init__(self, index, layout=None, prob_attack=0.99, prob_scaredFlee=0.99, samples=500, degree=-7):
        GhostAgent.__init__(self, index)
        self.index = index
        self.layout = layout
        self.degree = degree
        print("PRM ghost Index: ", index)
        self.start = layout.agentPositions[index][1]
        self.start = (round(self.start[0], 3), round(self.start[1], 3))
        print(self.start)
        self.prob_attack = prob_attack
        self.prob_scaredFlee = prob_scaredFlee
        self.buildPRM(samples)
        self.prm.add([self.start])
        self.establish_edges()
        self.next_node = self.start

    def getDistribution(self, state):
        ghost_state = state.getGhostState(self.index)
        legal_actions = state.getLegalActions(self.index)
        pos = state.getGhostPosition(self.index)
        is_scared = ghost_state.scaredTimer > 0
        speed_rnd = lambda: random.uniform(0.2, 1.0)
        speed = speed_rnd()
        if is_scared: speed = speed_rnd() * 0.5
        action_vectors = [Actions.directionToVector(a, speed) for a in legal_actions]
        new_positions = [(pos[0] + a[0], pos[1] + a[1]) for a in action_vectors]
        pacman_position = state.getPacmanPosition()
        # pacman_position = (round(pacman_position[0], 3), round(pacman_position[1], 3))
        pacman_position = (ceil(pacman_position[0]), ceil(pacman_position[1]))
        if self.is_in_node(pos):
            self.add_to_prm(pacman_position)
            self.next_node = self.find_next_node(pos, pacman_position)

        # Select best actions given the state
        distances_to_next_node = [manhattanDistance(pos, self.next_node) for pos in new_positions]
        # print "distances to next nodes", distances_to_next_node
        if is_scared:
            best_score = max(distances_to_next_node)
            best_prob = self.prob_scaredFlee
        else:
            best_score = min(distances_to_next_node)
            best_prob = self.prob_attack
        best_actions = [action for action, distance in zip(legal_actions, distances_to_next_node) if
                        distance == best_score]
        # Construct distribution
        dist = util.Counter()
        for a in best_actions: dist[a] = best_prob / len(best_actions)
        for a in legal_actions: dist[a] += (1 - best_prob) / len(legal_actions)
        dist.normalize()
        open('prm_edges_for_ghost_' + str(self.index) + '.txt', 'w').write(str(self.prm.edges))
        open('prm_vertices_for_ghost_' + str(self.index) + '.txt', 'w').write(str(self.prm.vertices))
        return dist

    def find_next_node(self, pos, pacman_position):
        path = self.prm.dijkstra(pos, pacman_position)
        if path is None:
            v = (round(random.uniform(1, self.layout.width - 1), 3), round(random.uniform(1, self.layout.height - 1), 3))
            self.add_to_prm(v)
            return self.next_node
        return path[1]

    #### PRM ####
    def sample_space(self, width, height, n):
        samples = []
        for i in range(n):
            samples.append((round(random.uniform(1, width - 1), 3), round(random.uniform(1, height - 1),
                                                                          3)))  # round to 3 decimal places means a tolerance of 0.001
        return samples

    def order_by_distance(self, v):
        return sorted(self.prm.vertices, key=lambda x: manhattanDistance(v, x))

    def establish_edges(self):  # connect each node to some of it's nearest neighbors
        for v in self.prm.vertices:
            d = self.degree
            for w in self.order_by_distance(v):
                if d == 0:
                    break
                if not self.collision(v, w):
                    self.prm.connect(self.prm.vertices[v], self.prm.vertices[w])
                    d -= 1

    def buildPRM(self, num_samples=100):
        samples = self.sample_space(self.layout.width, self.layout.height, num_samples)
        print("samples: ", samples)
        self.prm = Roadmap(samples)
        print("prm: ", self.prm.vertices)
        print(self.prm.vertices[samples[0]].edges)
        self.establish_edges()
        # save prm edges to a file to view
        with open('prm_edges_for_ghost_' + str(self.index) + '.txt', 'w') as f:
            f.write(str(self.prm.edges))

    def add_to_prm(self, v,):
        """In order to avoid adding too many nodes (slows the game) we only add a node it if's far enough from the
        closest node or if they have a wall between them"""
        v = (round(v[0], 3), round(v[1], 3))
        self.prm.add([v])
        neighbors = self.order_by_distance(v)
        d = self.degree
        for w in neighbors:
            if d == 0:
                break
            if not self.collision(v, w):
                # print("adding edge: ", v, w)
                self.prm.connect(self.prm.vertices[v], self.prm.vertices[w])
                d -= 1

    def not_wall(self, (x, y)):
        """it's probably not a wall"""
        if x == int(x) and y == int(y):
            if self.layout.isWall((x, y)):
                return True
        return False

    def is_in_node(self, v, tolerance=1):
        """check if a vertex is in a node"""
        x, y = round(v[0], 3), round(v[1], 3)
        xs = map(lambda x: round(x[0], 3), self.prm.vertices.keys())
        ys = map(lambda x: round(x[1], 3), self.prm.vertices.keys())
        for i in range(len(xs)):
            if manhattanDistance((x, y), (xs[i], ys[i])) < tolerance:
                return True
        return False

    def collision(self, start, end):
        """
        Returns true if there is a wall between the two points going in two stright lines (kinda, i think.)
        """
        walls = self.layout.walls
        x1, y1 = start
        x2, y2 = end
        x1 = int(floor(x1))
        x2 = int(floor(x2))
        y1 = int(floor(y1))
        y2 = int(floor(y2))

        if walls[x1][y1] or walls[x2][y2]:
            return True

        p1 = (x1, y1)
        p2 = (x2, y2)
        line_pix = bresenham(p1, p2)

        for p in line_pix:
            (x, y) = p
            if walls[x][y]:
                return True

        return False

#### Flank ghost ####
'''A ghost that tries to flank pacman'''


class FlankGhost(PRMGhost):

    def __init__(self, index, state=None, prob_attack=0.99, prob_scaredFlee=0.99, samples=100, degree=7):
        PRMGhost.__init__(self, index, state, prob_attack, prob_scaredFlee, samples, degree)
        self.prevpacman = state.agentPositions[0][1]

    def getDistribution(self, state):
        other_locations = []
        for agent in range(1, len(state.data.agentStates)):
            if agent != self.index:
                other_locations.append(state.data.agentStates[agent].configuration.pos)

        ghost_state = state.getGhostState(self.index)
        legal_actions = state.getLegalActions(self.index)
        pos = state.getGhostPosition(self.index)
        is_scared = ghost_state.scaredTimer > 0
        speed_rnd = lambda: random.uniform(0.2, 1.0)
        speed = speed_rnd()
        if is_scared: speed = speed_rnd() * 0.5
        action_vectors = [Actions.directionToVector(a, speed) for a in legal_actions]
        new_positions = [(pos[0] + a[0], pos[1] + a[1]) for a in action_vectors]
        pacman_position = state.getPacmanPosition()
        pacman_position = (round(pacman_position[0], 3), round(pacman_position[1], 3))
        pacman_position = (pacman_position[0] if floor(pacman_position[0]) > 0 else 1,
                           pacman_position[1] if floor(pacman_position[1]) > 0 else 1)

        if self.is_in_node(pos):
            self.add_to_prm(pacman_position)
            if (pacman_position[0] + 10 * (pacman_position[0] - self.prevpacman[0])) < self.layout.width and (
                    pacman_position[0] + 10 * (pacman_position[0] - self.prevpacman[0])) > 0:
                next_x = pacman_position[0] + 10 * (pacman_position[0] - self.prevpacman[0])
            else:
                next_x = pacman_position[0]
            if (pacman_position[1] + 10 * (pacman_position[0] - self.prevpacman[0])) < self.layout.height and (
                    pacman_position[1] + 10 * (pacman_position[0] - self.prevpacman[0])) > 0:
                next_y = pacman_position[1] + 10 * (pacman_position[0] - self.prevpacman[0])
            else:
                next_y = pacman_position[1]

            self.next_node = self.find_next_node(pos, (next_x, next_y))

        # Select best actions given the state
        distances_to_next_node = [manhattanDistance(pos, self.next_node) for pos in new_positions]
        # print "distances to next nodes", distances_to_next_node
        if is_scared:
            best_score = max(distances_to_next_node)
            best_prob = self.prob_scaredFlee
        else:
            best_score = min(distances_to_next_node)
            best_prob = self.prob_attack
        best_actions = [action for action, distance in zip(legal_actions, distances_to_next_node) if
                        distance == best_score]
        # Construct distribution
        dist = util.Counter()
        for a in best_actions: dist[a] = best_prob / len(best_actions)
        for a in legal_actions: dist[a] += (1 - best_prob) / len(legal_actions)
        dist.normalize()
        open('prm_edges_for_ghost_' + str(self.index) + '.txt', 'w').write(str(self.prm.edges))
        open('prm_vertices_for_ghost_' + str(self.index) + '.txt', 'w').write(str(self.prm.vertices))
        self.update_prevpacman(state)
        return dist

    def update_prevpacman(self, state):
        pacman_position = state.getPacmanPosition()
        pacman_position = (round(pacman_position[0], 3), round(pacman_position[1], 3))
        self.prevpacman = pacman_position

#### A* ghost ####
'''A ghost that uses A* to find the shortest path to pacman'''
class AStarGhost(PRMGhost):

    def __init__(self, index, state=None, prob_attack=0.99, prob_scaredFlee=0.99, samples=100, degree=7):
        PRMGhost.__init__(self, index, state, prob_attack, prob_scaredFlee, samples, degree)

    def find_next_node(self, pos, pacman_position):
        path = self.prm.a_star(pos, pacman_position)
        if path is None:
            v = (round(random.uniform(1, self.layout.width - 1), 3), round(random.uniform(1, self.layout.height - 1), 3))
            self.add_to_prm(v)
            return self.next_node
        return path[1]

class GridGhost(GhostAgent):
    """
     A ghost that only knows the world via a Grid, but not the actual grid   """

    def __init__(self, index, layout=None, prob_attack=0.99, prob_flee=0.99, grid_size=5):
        GhostAgent.__init__(self, index)
        self.index = index
        print("Grid ghost Index: ", index)
        self.layout = layout
        self.start = layout.agentPositions[index][1]
        print(self.start)
        self.prob_attack = prob_attack
        self.prob_flee = prob_flee
        self.grid_size = grid_size
        self.grid = None
        self.build_grid()
        self.next_tile = [self.position_to_grid(self.start)[0], self.position_to_grid(self.start)[1]]

    def getDistribution(self, state):
        ghost_state = state.getGhostState(self.index)
        legal_actions = state.getLegalActions(self.index)
        pos = state.getGhostPosition(self.index)
        is_scared = ghost_state.scaredTimer > 0
        speed_rnd = lambda: random.uniform(0.2, 1.0)
        speed = speed_rnd()
        if is_scared: speed = speed_rnd() * 0.5
        action_vectors = [Actions.directionToVector(a, speed) for a in legal_actions]
        new_positions = [(pos[0] + a[0], pos[1] + a[1]) for a in action_vectors]
        pacman_position = state.getPacmanPosition()
        pacman_position = (round(pacman_position[0], 3), round(pacman_position[1], 3))
        if self.position_to_grid(pos) == self.next_tile :
            self.next_tile = self.find_next_tile(pos, pacman_position)
        # Select best actions given the state
        distances_to_next_node = [manhattanDistance(pos, self.grid_to_position(self.next_tile)) for pos in new_positions]
        # print "distances to next nodes", distances_to_next_node
        if is_scared:
            best_score = max(distances_to_next_node)
            best_prob = self.prob_flee
        else:
            best_score = min(distances_to_next_node)
            best_prob = self.prob_attack
        best_actions = [action for action, distance in zip(legal_actions, distances_to_next_node) if
                        distance == best_score]
        # Construct distribution
        dist = util.Counter()
        for a in best_actions: dist[a] = best_prob / len(best_actions)
        for a in legal_actions: dist[a] += (1 - best_prob) / len(legal_actions)
        dist.normalize()
        return dist

    def build_grid(self):                               # Create a Grid and find which tiles have obstacles to avoid
        height = self.grid_size
        width = self.grid_size * self.layout.width / self.layout.height
        if height < 1 or width < 1:
            return
        self.grid = np.ones((height, width), bool)
        print 'build grid board size: {}, {}'.format(self.layout.width , self.layout.height)
        for i in range(height):
            for j in range(width):
                for m in range(int(floor(i*self.layout.height/height)), int(ceil((i+1)*self.layout.height/height))):
                    for n in range(int(floor(j*self.layout.width/width)), int(ceil((j+1)*self.layout.width/width))):
                        #print 'build grid checking point: {}, {}'.format(m, n)
                        if self.layout.isWall((i, j)):
                            self.grid[i, j] = False

    def find_next_tile(self, pos, pacman_position):     # Call dfs on the grid to find the next tile to move to
        next_tile = self.dfs_on_grid(pos, pacman_position)
        if next is None:
            self.grid_size += 5                         # If no tile is found make grid finer
            self.build_grid()
            return self.next_tile
        return next_tile

    def position_to_grid(self, pos):    # Find which tile contains a position on the board
        m = self.grid_size
        n = self.grid_size * self.layout.width / self.layout.height
        x = floor(pos[0] * n / self.layout.height)
        y = floor(pos[1] * m / self.layout.width)
        return x, y

    def grid_to_position(self, pos):    # Find the positions on the board in the middle of a tile
        m = self.grid_size
        n = self.grid_size * self.layout.width / self.layout.height
        x = floor(pos[0] * self.layout.height / n)
        y = floor(pos[1] * self.layout.width / m)         ### add 0.5
        return x, y

    def dfs_on_grid(self, start, end):
        queue = [(end[0], end[1])]
        visited = set()
        while queue:
            v = queue.pop(0)
            if v in visited:
                continue
            visited.add(v)
            if manhattanDistance(v, start) < 2:
                return v
            neighbor_cells = ((1, 0), (0, 1), (-1, 0), (0, -1))
            neighbors = list()
            for n in neighbor_cells:
                x, y = int(v[0])+n[0], int(v[1])+n[1]
                if 0 <= x <= self.grid_size * self.layout.width / self.layout.height and 0 <= y <= self.grid_size:
                    if self.grid[int(v[0])+n[0], int(v[1])+n[1]]:
                        neighbors.append(int((v[0])+n[0], int(v[1])+n[1]))
            for u in neighbors:
                if u not in visited:
                    queue.append(v)
        # print('No path found between {} and {}'.format(start, end))
        return None