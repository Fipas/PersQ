from __future__ import division

import time
import math
import random
import instance


class TreeNode():
    def __init__(self, state, parent):
        self.state = state
        self.parent = parent
        self.num_visits = 0
        self.total_reward = 0
        self.is_fully_expanded = False
        self.children = {}


class MCTS():
    def __init__(self, iteration_limit, exploration_constant=1 / math.sqrt(2)):
        self.iteration_limit = iteration_limit
        self.exploration_constant = exploration_constant

    def search(self, initial_state, final_state, budget, distance_matrix, pois,
        user, queue_time, excluded_sequence=None):
        self.root = TreeNode(initial_state, None)
        self.initial_state = initial_state
        self.budget = budget
        self.i_list = []
        self.distance_matrix = distance_matrix
        self.pois = pois
        self.user = user
        self.queue_time = queue_time
        self.excluded_sequence = excluded_sequence

        for i in range(self.iteration_limit):
            i_temp = []
            i_temp.append(self.root.state)
            total_cost = 0
            a_i = self.root
            a_j = None
            #print(self.budget)

            while total_cost < self.budget:
                if len(i_temp) == len(self.pois):
                    break

                if (a_i.is_fully_expanded):
                    #a_j = self.select_node(a_i, i_temp, total_cost)
                    a_j = self.select_node(a_i, i_temp, len(i_temp))
                else:
                    #a_j = self.expand(a_i, i_temp, total_cost)
                    a_j = self.expand(a_i, i_temp, len(i_temp))

                i_temp.append(a_j.state)
                total_cost += (self.distance_matrix.get_walking_time(a_i.state, a_j.state) + 
                self.pois[a_i.state].ride_duration + 
                #queue_time.get_queue(total_cost, a_j.state))
                queue_time.get_queue(len(i_temp), a_j.state))

                if a_j.state == final_state:
                    break

                a_i = a_j
        

            self.backprop_visits(a_j)

            if a_j is not None and a_j.state == final_state:
                reward = self.simulate(i_temp)
                self.backprop_reward(a_j, reward)
                self.i_list.append((i_temp, reward))
            

        best_score = -1
        best_itinerary = None

        for el in self.i_list:
            if el[1] > best_score:
                best_score = el[1]
                best_itinerary = el[0]
        
        return best_itinerary

    def expand(self, node, itinerary, total_time):
        #print('expand')
        for poi in self.pois.values():
            if poi.poi_id in itinerary:
                continue
            a_j = poi.poi_id
            if a_j not in node.children:
                new_node = TreeNode(a_j, node)
                node.children[a_j] = new_node
                if len(self.pois) == len(node.children):
                    node.is_fully_expanded = True
                return new_node
        
        return self.select_node(node, itinerary, total_time)

    def select_node(self, node, itinerary, total_time):
        #print('select')
        a_n = None
        uct_max = 0

        for poi in self.pois.values():
            if poi.poi_id in itinerary:
                continue

            a_j = poi.poi_id
            
            if a_j not in node.children:
                raise Exception('forbidden')
                new_node = TreeNode(a_j, node)
                node.children[a_j] = new_node
                cur_node = new_node
            else:
                cur_node = node.children[a_j]

            #print(itinerary)
            #print(a_j)
            interest_a_j = self.user.get_interest(self.pois[a_j].get_category(), self.excluded_sequence)
            populariy_a_j = self.pois[a_j].popularity
            travel_time = self.distance_matrix.get_walking_time(node.state, a_j)
            ride_duration_a_j = self.pois[a_j].ride_duration
            queue_time = self.queue_time.get_queue(total_time, a_j)

            exploit_a_j = ((cur_node.total_reward / cur_node.num_visits) +
                    ((interest_a_j + populariy_a_j) / (travel_time + ride_duration_a_j + queue_time)))

            explore_a_j = (2 * self.exploration_constant * 
                math.sqrt((2 * math.log(node.num_visits)) / cur_node.num_visits))

            uct_a_j = exploit_a_j + explore_a_j
            #print(uct_a_j)

            if uct_a_j >= uct_max:
                uct_max = uct_a_j
                a_n = cur_node

        return a_n 


    def simulate(self, itinerary):
        reward = 0

        for poi in itinerary:
            interest = self.user.get_interest(self.pois[poi].get_category(), self.excluded_sequence)
            popularity = self.pois[poi].popularity

            reward += interest + popularity

        return reward


    def backprop_visits(self, node):
        while node is not None:
            node.num_visits += 1
            node = node.parent

    
    def backprop_reward(self, node, reward):
        while node is not None:
            node.total_reward += reward
            node = node.parent