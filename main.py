import csv
import os
from haversine import haversine
from mcts import mcts
from copy import deepcopy

running_dir = os.path.dirname(os.path.abspath(__file__))

theme_parks = ["caliAdv", "disHolly", "disland", "epcot", "MagicK"]
pois = {}
users = {}
popularity = {}
distance_matrix = {}


class User:
	def __init__(self, user_id):
		self.user_id = user_id
		self.sequences = []

	def add_sequence(self, sequence):
		self.sequences.append(sequence)

class Sequence:
	def __init__(self, seq_iq):
		self.seq_iq = seq_iq
		self.visits = []

	def add_visit(self, visit):
		self.visits.append(visit)

class Visit:
	def __init__(self, poi_id):
		self.poi_id = poi_id
		self.arrival_time = -1
		self.departure_time = -1
		self.duration = 0
		self.num_photos = 0

	def update_duration(self, timestamp):
		self.num_photos += 1

		if self.arrival_time == -1 and self.departure_time == -1:
			self.arrival_time = timestamp
			self.departure_time = timestamp
		else:
			self.departure_time = timestamp

		self.duration = self.departure_time - self.arrival_time


class POI:
	def __init__(self, poi_id, poi_name, ride_duration, lat, lng, category, popularity):
		self.poi_id = poi_id
		self.poi_name = poi_name
		self.ride_duration = ride_duration * 60
		self.lat = lat
		self.lng = lng
		self.category = category
		self.popularity = popularity



class DistanceMatrix:
	def __init__(self, num_pois):
		self.distance_matrix = {}
		self.walking_time = {}
		#print num_pois
		for i in range(1, num_pois + 1):
			self.distance_matrix[i] = {}
			self.walking_time[i] = {}
			for j in range(1, num_pois + 1):
				self.distance_matrix[i][j] = 0
				self.walking_time[i][j] = 0

	def set_distance(self, source, destination, distance):
		self.distance_matrix[source][destination] = distance
		self.distance_matrix[destination][source] = distance

	def get_distance(self, source, destination):
		return float(self.distance_matrix[source][destination])

	def set_walking_time(self, source, destination, walking_time):
		self.walking_time[source][destination] = walking_time
		self.walking_time[destination][source] = walking_time

	def get_walking_time(self, source, destination):
		return float(self.distance_matrix[source][destination])



def load_pois():
	for park in theme_parks:
		cost_profit_file = open('{}/data/costProf-sigir17/costProfCat-{}-all.csv'.format(running_dir, park))
		poi_list_file = open('{}/data/poiList-sigir17/POI-{}.csv'.format(running_dir, park))
		user_visits_file = open('{}/data/userVisits-sigir17/userVisits-{}-allPOI.csv'.format(running_dir, park))

		cost_profit_data = csv.DictReader(cost_profit_file, delimiter=';')
		pois_list_data = csv.DictReader(poi_list_file, delimiter=';')
		user_visits_data = csv.DictReader(user_visits_file, delimiter=';')

		pois[park] = {}
		distance_matrix[park] = DistanceMatrix(50)
		#pppopularity = {}

		for row in cost_profit_data:
			#print row
			#pppopularity[int(row["to"])] = int(row["popularity"])
			source = int(row["from"])
			destination = int(row["to"])
			distance_matrix[park].set_distance(source, destination, row["distance"])
			distance_matrix[park].set_walking_time(source, destination, row["walkTime"])


		for row in pois_list_data:
			categories = []
			categories.append(row["theme"])
			categories.append(row["theme2"])
			categories.append(row["theme3"])
			categories.append(row["theme4"])

			'''
			if int(row["poiID"]) == 2:
				pppopularity[int(row["poiID"])] = 0

			print "{} {}".format(popularity[park][int(row["poiID"])], pppopularity[int(row["poiID"])])
			'''

			pois[park][int(row["poiID"])] = POI(int(row["poiID"]), row["poiName"], float(row["rideDuration"]),
								float(row["lat"]), float(row["long"]), categories, popularity[park][int(row["poiID"])])

		for poi_i in pois[park]:
			for poi_j in pois[park]:
				if poi_i != poi_j and distance_matrix[park].get_distance(poi_i, poi_j) == 0:
					poi_i_lat_lng = (pois[park][poi_i].lat, pois[park][poi_i].lng)
					poi_j_lat_lng = (pois[park][poi_j].lat, pois[park][poi_j].lng)

					distance = haversine(poi_i_lat_lng, poi_j_lat_lng)
					walking_time = distance / 1,38889
					distance_matrix[park].set_distance(poi_i, poi_j, distance)
					distance_matrix[park].set_walking_time(poi_i, poi_j, walking_time)



		cost_profit_file.close()
		poi_list_file.close()
		user_visits_file.close()

def process_user_visits():
	for park in theme_parks:
		user_visits_file = open('{}/data/userVisits-sigir17/userVisits-{}-allPOI.csv'.format(running_dir, park))
		user_visits_data = csv.DictReader(user_visits_file, delimiter=';')

		users[park] = {}

		old_user_id = -1
		old_poi_id = -1
		old_seq_id = -1
		popularity[park] = [0] * 50


		for row in user_visits_data:
			user_id = row["nsid"]
			poi_id = int(row["poiID"])
			seq_id = int(row["seqID"])

			if user_id != old_user_id:
				user = User(user_id)
				sequence = Sequence(seq_id)
				visit = Visit(poi_id)
				sequence.add_visit(visit)
				user.add_sequence(sequence)
				users[park][user_id] = user
			elif seq_id != old_seq_id:
				sequence = Sequence(seq_id)
				visit = Visit(poi_id)
				sequence.add_visit(visit)
				user.add_sequence(sequence)
			elif poi_id != old_poi_id:
				visit = Visit(poi_id)
				sequence.add_visit(visit)

			popularity[park][poi_id] += 1
			visit.update_duration(int(row["takenUnix"]))
			#print visit.duration

			old_user_id = user_id
			old_poi_id = poi_id
			old_seq_id = seq_id


		n_photos = 0
		n_users = 0
		n_visits = 0
		n_sequences = 0

		n_users = len(users[park])

		for user_key in users[park]:
			user = users[park][user_key]
			n_sequences += len(user.sequences)
			for sequence in user.sequences:
				n_visits += len(sequence.visits)
				for visit in sequence.visits:
					print "{} {} {}".format(park, user_key, visit.duration)
					n_photos += visit.num_photos


		#print "{}: {} {} {} {}".format(park, n_photos, n_users, n_visits, n_sequences)
		user_visits_file.close()

process_user_visits()
load_pois()


class PersQState():
	def __init__(self, num_pois, starting_poi, ending_poi):
		self.i_temp = []
		self.reward = 0
		self.total_cost = 0
		self.t_visits = [0] * (num_pois + 1)
		self.t_rewards = [0] * (num_pois + 1)
		self.num_pois = num_pois
		self.i_temp.append(starting_poi)
		self.t_visits[starting_poi] = 1
		self.ending_poi = ending_poi


	def getPossibleActions(self):
		if self.isTerminal():
			return []

		possibleActions = [i for i in range(1, (self.num_pois + 1))]
		#for i in range(len(self.board)):
		#	for j in range(len(self.board[i])):
		#		if self.board[i][j] == 0:
		#			possibleActions.append(Action(player=self.currentPlayer, x=i, y=j))
		return possibleActions

	def takeAction(self, action):
		newState = deepcopy(self)
		old_poi = self.i_temp[len(self.i_temp) - 1]
		newState.i_temp.append(action)
		print distance_matrix["MagicK"].get_distance(old_poi, action)
		print pois["MagicK"][action].ride_duration
		newState.reward = distance_matrix["MagicK"].get_distance(old_poi, action) + pois["MagicK"][action].ride_duration
		return newState

	def isTerminal(self):
		if self.i_temp[len(self.i_temp) - 1] == self.ending_poi:
			return True
		else:
			return False

	def getReward(self):
		if self.isTerminal():
			return self.reward
		else:
			return False

initialState = PersQState(len(pois["MagicK"]), 3, 4)
mcts = mcts(timeLimit=1000)
bestAction = mcts.search(initialState=initialState)

print bestAction