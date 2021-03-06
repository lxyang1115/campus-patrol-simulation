import numpy as np
import pandas as pd
from plotgraph import PlotGraph
import simpy
import random
from graph_init import init
import os.path
import matplotlib.pyplot as plt


def createMarkovMatrix(p, t, d, method):
    if method == "DCP":
        matrix = np.zeros((2*d+1, 2*d+1))
        matrix[2*d][2*d] = 1
        for i in range(0, 2*d):
            if i % 2 == 0:
                matrix[i, i + 2] = p
                matrix[i, i + 1] = 1 - p
            else:
                matrix[i][i-1] = 1 - p
                if i - 2 > 0:
                    matrix[i][i-2] = p
                else:
                    matrix[i][i-1+2*d] = p
            # matrix[i][max(i+1,2*d)] = p
            # matrix[i][min(0,i-2)] = 1 - p
        return matrix
    elif method == "DNCP":
        matrix = np.zeros((2*d+1, 2*d+1))
        matrix[2*d][2*d] = 1
        for i in range(0, 2*d):
            if i % 2 == 0:
                matrix[i][i+2] = p
                if i != 0:
                    matrix[i][i-1] = 1-p
                else:
                    matrix[i][2*d] = 1 - p
            else:
                if i != 1:
                    matrix[i][i - 2] = p
                else:
                    matrix[i][2*d] = p
                matrix[i][i+1] = 1 - p
        return matrix
    elif method == "BMP":
        matrix = np.zeros((d+1, d+1))
        for i in range(0, d):
            matrix[i][i+1] = 1 - p
            if i == 0:
                matrix[i][d] = p
            else:
                matrix[i][i-1] = p
        matrix[d][d] = 1
        return matrix


def cal_ppd(p, t, d, method):
    matrix = createMarkovMatrix(p, t, d, method)
    # if method == "BMP":
    #     print(matrix)
    # print(matrix)
    result = matrix
    for i in range(t-1):
        result = np.matmul(result, matrix)

    Res = np.zeros(shape=(d, 1))
    if method == "DCP" or method == "DNCP":
        for i in range(d):
            Res[i] = result[2 * i + 1][2*d]
    elif method == "BMP":
        for i in range(d):
            Res[i] = result[i][d]
    return np.min(Res)


# Markov????????????
def CalculateOptimalP(t, d, method="DNCP"):
    max_ppd = 0
    for i in range(100):
        p = i/100
        # print(p)
        x = cal_ppd(p, t, d, method)
        if x > max_ppd:
            index = i
            max_ppd = x
    # print(method)
    # print(max_ppd)
    return index/100


# ??????????????????
class AntsTSP:
    def __init__(self, d, n) -> None:
        # ???????????????
        self.m = 50                                  # ????????????
        self.alpha = 1                               # ?????????????????????
        self.beta = 5                                # ????????????????????????
        self.rho = 0.3                               # ?????????????????????
        self.q = 1                                   # ?????????
        self.pro = 0.2                               # ??????????????????
        self.eta = 1./d                              # ????????????
        self.tau = np.ones((n, n))                   # ???????????????
        self.iter_max = 200                         # ??????????????????
        self.in_iter_max = 20                        # ????????????????????????
        self.route_best = []                         # ??????????????????
        self.length_best = np.zeros(self.iter_max)        # ????????????????????????
        self.length_ave = np.zeros(self.iter_max)         # ??????????????????


# ?????????
class Graph:
    def __init__(self, matrix, node_dict):
        self.matrix = matrix.copy()         # ????????????
        self.n = len(matrix)                # ????????????
        self.node_dict = node_dict
        self.distance = None                # ???????????????????????????
        self.pre_node = None                # ????????????????????????????????????
        # if matrix is not None:
        # self.matrix = matrix.copy()
        # self.n = len(matrix)
        self.Floyd()

    def changeMatrix(self, new_matrix):
        self.matrix = new_matrix.copy()
        self.n = len(new_matrix)
        self.Floyd()

    def readFromCsv(self, file_name):           # ????????????
        graph = pd.read_csv(file_name, header=None)
        graph = np.array(graph)
        graph[np.isnan(graph)] = np.inf
        self.matrix = graph.copy()
        self.n = len(self.matrix)
        self.Floyd()

    def Floyd(self):                    # ????????????????????????????????????
        D = self.matrix.copy()
        lengthD = self.n
        P = [[i if self.matrix[i][j] != np.inf else -
              1 for j in range(lengthD)] for i in range(lengthD)]
        for k in range(lengthD):
            for i in range(lengthD):
                for j in range(lengthD):
                    if D[i][j] > D[i][k] + D[k][j]:         # ??????????????????????????????????????????????????????????????????
                        P[i][j] = P[k][j]                 # ????????????????????????
                        D[i][j] = D[i][k] + D[k][j]
        self.distance = D.copy()
        self.pre_node = P.copy()

    def getDistance(self, start, end):          # ?????????????????????????????????
        return self.distance[start][end]

    def getPath(self, start, end):              # ??????????????????????????????????????????
        res = [end]
        while res[0] != start:
            res = [self.pre_node[start][res[0]]] + res
        return res

    def getShortestCircle(self, test=False, file_name="tsp_result.txt"):                # TSP????????????
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0 and not test:
            file = open(file_name, 'r')         # ????????????
            contents = file.readlines()
            l = float(contents[0])
            self.circle = np.array([int(i) for i in contents[1:]])      # ?????????
            self.min_length = l
            print(float(format(l, ".1f")), '\n', self.circle)
            file.close()
            return self.circle, self.min_length
        d = self.distance.copy()
        d[d == 0] = 1e-6
        self.ants = AntsTSP(d, self.n)
        iter = 0
        # ?????????????????????
        while iter < self.ants.iter_max:
            # ???????????????????????????????????????
            start = np.random.randint(0, self.n, size=self.ants.m)
            table = []
            length = np.zeros(self.ants.m) + np.inf
            for i in range(0, self.ants.m):
                path = [start[i]]           # ????????????
                l = 0                       # ????????????
                while len(set(path)) < self.n:
                    # print(len(set(path)), in_iter)
                    now = path[-1]
                    noPass = [x for x in range(self.n) if x not in path]
                    p = [self.ants.tau[now, j]**self.ants.alpha + self.ants.eta[now, j]**self.ants.beta
                         if j in noPass else 0 for j in range(self.n)]
                    p = p / np.sum(p)
                    # ???????????????????????????????????????
                    ps = np.cumsum(p)
                    target = np.argmax(ps > np.random.rand())
                    # ???????????????????????????????????????????????????????????????
                    path += self.getPath(now, target)[1:]
                    l += self.getDistance(now, target)
                # ????????????
                l += self.getDistance(path[-1], path[0])
                path += self.getPath(path[-1], path[0])[1:]
                table.append(path)
                length[i] = l
            # ???????????????????????????????????????
            min_length = np.min(length)
            min_index = np.argmin(length)
            self.ants.length_ave[iter] = np.average(length)
            self.ants.length_best[iter] = min_length \
                if (iter == 0 or min_length <= self.ants.length_best[iter-1]) \
                else self.ants.length_best[iter-1]
            self.ants.route_best.append(table[min_index]
                                        if self.ants.length_best[iter] == min_length else self.ants.route_best[-1])
            # print(min_length)
            # ???????????????
            delta_tau = np.zeros((self.n, self.n))
            for i in range(self.ants.m):
                for j in range(np.size(table[i])-1):
                    delta_tau[table[i][j], table[i][j+1]
                              ] += self.ants.q / length[i]
            self.ants.tau = (1 - self.ants.rho) * self.ants.tau + delta_tau
            iter += 1

        plt.figure()
        plt.plot(range(self.ants.iter_max), self.ants.length_best)
        plt.show()
        shortest_length = min(self.ants.length_best)
        shortest_index = np.argmin(self.ants.length_best)
        shortest_route = self.ants.route_best[shortest_index][:-1]
        print(float(format(shortest_length, ".1f")), '\n', shortest_route)
        # while shortest_route[0] != 0:
        #     shortest_route.append(shortest_route.pop(0))
        # print(shortest_length, '\n', shortest_route)
        self.circle = shortest_route                    # ?????????
        self.min_length = shortest_length
        file = open(file_name, 'w+')                    # ?????????
        file.write(str(shortest_length))
        file.write('\n')
        for node in shortest_route:
            file.write(str(node))
            file.write('\n')
        file.close()
        return shortest_route, shortest_length


# ????????????
class Patroller:
    def __init__(self, init_position_index, graph, env, index, init_position, speed):
        global map_dict, movedata, direction
        self.route = graph.circle
        self.graph = graph
        self.node_dict = graph.node_dict
        self.position = init_position
        self.last_node = init_position_index            # ???????????????????????????????????????
        self.next_node = (self.last_node + direction +
                          len(self.route)) % len(self.route)    # ????????????
        self.speed = speed
        self.env = env
        self.index = index
        self.name = 'Robot %d' % index

        movedata[self.index][0].append(0)  # t
        movedata[self.index][1].append(init_position[0])  # x
        movedata[self.index][2].append(init_position[1])  # y
        # print(self.name, "arrived", init_position, "at", self.env.now)

    # ??????????????????
    def move(self):
        global map_dict, movedata, direction
        while True:
            # ?????????????????????????????????
            last_node_position = self.node_dict[self.route[self.last_node]]
            # ???????????????????????????????????????
            next_node_position = self.node_dict[self.route[self.next_node]]
            # ??????????????????????????????????????????????????????????????????????????????
            # assert (self.position[1] - last_node_position[1]) * (next_node_position[0] - last_node_position[0]) - (
            #     next_node_position[1] - last_node_position[1])*(self.position[0]-last_node_position[0]) < 5
            # ??????????????????????????????????????????
            dist_to_next = np.sqrt(
                np.sum((next_node_position - self.position)**2))
            if dist_to_next / self.speed < 1:
                # ??????1s???????????????
                movetime = dist_to_next / self.speed
                movetime1 = float(format(movetime, '.1f'))
                yield env.timeout(movetime1)
                self.position = next_node_position

                movedata[self.index][0].append(self.env.now)
                movedata[self.index][1].append(self.position[0])
                movedata[self.index][2].append(self.position[1])
                # print(self.name, "arrived", self.position,
                #       "at", float(format(self.env.now, '.1f')))
                self.last_node = self.next_node
                self.next_node = (self.last_node + direction +
                                  len(self.route)) % len(self.route)
                self.detect()

                yield env.timeout(1-movetime1)
                movetime = 1 - movetime1
                last_node_position = self.node_dict[self.route[self.last_node]]

                next_node_position = self.node_dict[self.route[self.next_node]]

                self.position = self.position + movetime * self.speed * (next_node_position -
                    last_node_position)/(np.sqrt(np.sum((next_node_position - last_node_position)**2)))
                dist_to_next = np.sqrt(
                    np.sum((next_node_position - self.position)**2))
                movedata[self.index][0].append(self.env.now)
                movedata[self.index][1].append(self.position[0])
                movedata[self.index][2].append(self.position[1])
                # print(self.name, "arrived", self.position,
                #       "at", float(format(self.env.now, '.1f')))

            else:
                # ??????1s
                movetime = 1
                # movetime1 = float(format(movetime, '.1f'))  # ????????????????????????

                yield env.timeout(1)
                self.position = self.position + movetime * self.speed * (next_node_position -
                    last_node_position)/(np.sqrt(np.sum((next_node_position - last_node_position)**2)))
                dist_to_next = np.sqrt(
                    np.sum((next_node_position - self.position)**2))
                movedata[self.index][0].append(self.env.now)  # t
                movedata[self.index][1].append(self.position[0])  # x
                movedata[self.index][2].append(self.position[1])  # y

            if dist_to_next < 0.1*self.speed:
                self.position = next_node_position
                # print(self.name, "arrived", self.position,
                #       "at", float(format(self.env.now, '.1f')))
                self.last_node = self.next_node
                self.next_node = (self.last_node + direction +
                                  len(self.route)) % len(self.route)
                self.detect()
            if self.next_node != (self.last_node + direction +
                                  len(self.route)) % len(self.route):
                # ?????????????????????
                self.last_node, self.next_node = self.next_node, self.last_node

    def detect(self):
        # ???????????????????????????
        global thief_num, thievies, appear, thiefdata, map_dict, t, thief_cnt, catch_time
        for i in range(thief_num):
            if np.sqrt(np.sum((self.node_dict[thievies[i]] - self.position)**2)) < 50:
                time = self.env.now - appear[i]
                # ????????????t????????????????????????
                if time < t:
                    catch_time.append(self.env.now - appear[i])
                    thief_cnt[1] += 1
                    # print("catch thief", i, "after",
                    #       float(format(self.env.now - appear[i], '.1f')), "s")  # ??????????????????
                # ??????????????????
                thievies[i] = generateThief(1)[0]
                # print("thief", i, ':', thievies[i])
                appear[i] = self.env.now
                thiefdata[i]['%.2f' % self.env.now] = map_dict[thievies[i]]


# ????????????
def generateThief(thief_num):
    global robots, graph, route, thief_cnt
    thief_cnt[0] += thief_num
    node = list(range(graph.n))
    # ???????????????????????????
    for robot in robots:
        if route[robot.last_node] in node:
            node.remove(route[robot.last_node])
        if route[robot.next_node] in node:
            node.remove(route[robot.next_node])
    return random.sample(node, thief_num)


# ???????????????????????????
def checkDirection():
    global t, d, direction, posibility
    yield env.timeout(0.99)
    while True:
        if random.random() > posibility:
            # ??????
            direction = - direction
        yield env.timeout(1)


# ???????????????????????????????????????
def averagePos(graph, robot_num):
    l = graph.min_length / robot_num
    # print(l)
    route = graph.circle
    res = [[0, graph.node_dict[route[0]]]]
    sum_d = np.zeros(len(route))
    for i in range(1, len(route)):
        sum_d[i] = sum_d[i-1] + graph.matrix[route[i-1]][route[i]]
        num = int(sum_d[i]/l) - int(sum_d[i-1]/l)
        # print(num)
        last_node = graph.node_dict[route[i-1]]
        next_node = graph.node_dict[route[i]]
        unit_v = (next_node - last_node) / \
            np.sqrt(np.sum((next_node - last_node)**2))
        # print(unit_v)
        for j in range(num):
            # print((int(sum_d[i-1]/l+j+1)*l - sum_d[i-1]))
            pos = last_node + unit_v * (int(sum_d[i-1]/l+j+1)*l - sum_d[i-1])
            res.append([i-1, pos])
    return res


if __name__ == '__main__':
    # node_dict = {i: np.array(node_dict[i]) for i in node_dict.keys()}

    # matrix = np.array([[0, 40, np.inf, 40],
    #                    [40, 0, 40, np.inf],
    #                    [np.inf, 40, 0, 40],
    #                    [40, np.inf, 40, 0]])

    # node_dict = {i : np.array([25*(int)(i/5), 100-25*(int)(i%5)]) for i in range(25)}
    # map_dict = {i : node_dict[i]/25*160+10 for i in range(25)}
    # node_dict = map_dict

    # matrix = np.zeros((25,25)) + np.inf
    # for i in range(25):
    #     matrix[i][i] = 0
    #     if i % 5 != 0:
    #         matrix[i-1][i] = matrix[i][i-1] = 160
    #     if i % 5 != 4:
    #         matrix[i+1][i] = matrix[i][i+1] = 160
    #     if i >= 5:
    #         matrix[i-5][i] = matrix[i][i-5] = 160
    #     if i < 15:
    #         matrix[i+5][i] = matrix[i][i+5] = 160

    # ???????????????
    map_dict, matrix = init()
    node_dict = {i: np.array(map_dict[i]) for i in map_dict.keys()}

    graph = Graph(matrix, node_dict)
    route, length = graph.getShortestCircle()
    length /= 100
    
    robot_num = 8
    thief_num = 10

    robots = []
    movedata = [[[], [], []] for _ in range(robot_num)]

    # ?????????Markov??????
    direction = 1
    d = int(length / robot_num)
    t = int(d * 0.5)
    posibility = CalculateOptimalP(t, d)
    
    t = 10

    thief_cnt = [0, 0]
    catch_time = []

    # ????????????????????????
    env = simpy.Environment()
    initposs = averagePos(graph, robot_num)
    print(initposs)
    for i in range(robot_num):
        lastnode = initposs[i][0]
        initpos = initposs[i][1]
        robot = Patroller(lastnode, graph, env, i, initpos, 100)
        robots.append(robot)
        env.process(robot.move())

    env.process(checkDirection())
    
    # ????????????
    thievies = generateThief(thief_num)
    print("thief", thievies)
    appear = np.zeros(thief_num)
    thiefdata = [{} for _ in range(thief_num)]
    for i in range(thief_num):
        thiefdata[i]['%.2f' % 0] = map_dict[thievies[i]]

    # ???????????????61??????????????????????????????
    sim_time = 1001
    env.run(until=sim_time)
    # print(posibility)
    print("catch thieves prob: ", thief_cnt[1]/thief_cnt[0])
    print("average catch time: ", np.mean(catch_time))
    
    # ??????????????????
    # legend = ['Robot %d' % i for i in range(robot_num)] + \
    #     ['Thief %d' % j for j in range(thief_num)]
    
    # plotgraph = PlotGraph(robot_num=robot_num, thief_num=thief_num, legend=legend,
    #                       mapfile='.\graph.png')  #
    # plotgraph.plotshow(end_time=sim_time-1, movedata=movedata, thiefdata=thiefdata,
    #                    outpath='demo.mp4', dpi=240)


