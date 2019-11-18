import csv
import os
from haversine import haversine
from mcts import mcts
from copy import deepcopy
import math


class Instance():
	def __init__(self):
		self.running_dir = os.path.dirname(os.path.abspath(__file__))
		#self.theme_parks = ["caliAdv", "disHolly", "disland", "epcot", "MagicK"]
		self.theme_parks = ["caliAdv"]
		self.pois = {}
		self.users = {}
		self.queues = {}
		self.popularity = {}
		self.distance_matrix = {}
		self.process_user_visits()
		self.load_pois()
		self.process_queues()
		

	def process_queues(self):
		for park in self.theme_parks:
			self.queues[park] = POIQueue(len(self.pois[park]))
			for user in self.users[park].values():
				for sequence in user.sequences:
					self.queues[park].add_to_queue(sequence, self.pois[park])


	def load_pois(self):
		for park in self.theme_parks:
			cost_profit_file = open('{}/data/costProf-sigir17/costProfCat-{}-all.csv'.format(self.running_dir, park))
			poi_list_file = open('{}/data/poiList-sigir17/POI-{}.csv'.format(self.running_dir, park))
			#user_visits_file = open('{}/data/userVisits-sigir17/userVisits-{}-allPOI.csv'.format(self.running_dir, park))

			cost_profit_data = csv.DictReader(cost_profit_file, delimiter=';')
			pois_list_data = csv.DictReader(poi_list_file, delimiter=';')
			#user_visits_data = csv.DictReader(user_visits_file, delimiter=';')

			self.pois[park] = {}
			self.distance_matrix[park] = DistanceMatrix(50)
			#pppopularity = {}

			for row in cost_profit_data:
				#print row
				#pppopularity[int(row["to"])] = int(row["popularity"])
				source = int(row["from"])
				destination = int(row["to"])
				self.distance_matrix[park].set_distance(source, destination, row["distance"])
				self.distance_matrix[park].set_walking_time(source, destination, row["walkTime"])


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

				self.pois[park][int(row["poiID"])] = POI(int(row["poiID"]), row["poiName"], float(row["rideDuration"]),
									float(row["lat"]), float(row["long"]), categories, self.popularity[park][int(row["poiID"])])

			for poi_i in self.pois[park]:
				for poi_j in self.pois[park]:
					if poi_i != poi_j and self.distance_matrix[park].get_distance(poi_i, poi_j) == 0:
						poi_i_lat_lng = (self.pois[park][poi_i].lat, self.pois[park][poi_i].lng)
						poi_j_lat_lng = (self.pois[park][poi_j].lat, self.pois[park][poi_j].lng)

						distance = haversine(poi_i_lat_lng, poi_j_lat_lng)
						walking_time = distance / 1,38889
						self.distance_matrix[park].set_distance(poi_i, poi_j, distance)
						self.distance_matrix[park].set_walking_time(poi_i, poi_j, walking_time)



			cost_profit_file.close()
			poi_list_file.close()
			#user_visits_file.close()


	def process_user_visits(self):
		for park in self.theme_parks:
			user_visits_file = open('{}/data/userVisits-sigir17/userVisits-{}-allPOI.csv'.format(self.running_dir, park))
			user_visits_data = csv.DictReader(user_visits_file, delimiter=';')

			self.users[park] = {}

			old_user_id = -1
			old_poi_id = -1
			old_seq_id = -1
			self.popularity[park] = [0] * 50


			for row in user_visits_data:
				user_id = row["nsid"]
				poi_id = int(row["poiID"])
				seq_id = int(row["seqID"])
				taken = int(row["takenUnix"])
				poi_theme = row["poiTheme"]

				if user_id != old_user_id:
					user = User(user_id)
					sequence = Sequence(seq_id)
					visit = Visit(poi_id)
					sequence.add_visit(visit)
					user.add_sequence(sequence)
					self.users[park][user_id] = user
				elif seq_id != old_seq_id:
					sequence = Sequence(seq_id)
					visit = Visit(poi_id)
					sequence.add_visit(visit)
					user.add_sequence(sequence)
				elif poi_id != old_poi_id:
					visit = Visit(poi_id)
					sequence.add_visit(visit)

				sequence.add_photo(Photo(poi_id, taken, poi_theme))

				self.popularity[park][poi_id] += 1
				visit.update_duration(taken)
				#print visit.duration

				old_user_id = user_id
				old_poi_id = poi_id
				old_seq_id = seq_id


			n_photos = 0
			#n_users = 0
			n_visits = 0
			n_sequences = 0

			#n_users = len(self.users[park])

			for user_key in self.users[park]:
				user = self.users[park][user_key]
				n_sequences += len(user.sequences)
				for sequence in user.sequences:
					n_visits += len(sequence.visits)
					for visit in sequence.visits:
						#print("{} {} {}".format(park, user_key, visit.duration))
						n_photos += visit.num_photos


			#print "{}: {} {} {} {}".format(park, n_photos, n_users, n_visits, n_sequences)
			user_visits_file.close()


class User:
	def __init__(self, user_id):
		self.user_id = user_id
		self.sequences = []
		self.interest = {}
		self.interest_excluded = {}

	def add_sequence(self, sequence):
		self.sequences.append(sequence)
		self.interest_excluded[sequence] = {}

	def get_interest(self, category, excluded=None):
		if excluded == None and category in self.interest:
			return self.interest[category]

		#print(category)
		if excluded != None and category in self.interest_excluded[excluded]:
			return self.interest_excluded[excluded][category]

		interest = 0
		num_photos = 0
		for s in self.sequences:
			if s == excluded:
				continue
			for p in s.photos:
				num_photos += 1
				if p.category == category:
					interest += 1

		interest = float(interest) / num_photos
		
		if excluded == None:
			self.interest[category] = interest
		else:
			self.interest_excluded[excluded][category] = interest

		return interest
		

class Sequence:
	def __init__(self, seq_id):
		self.seq_id = seq_id
		self.visits = []
		self.photos = []
		self.duration = -1

	def get_initial_poi(self):
		return self.visits[0].poi_id

	def get_final_poi(self):
		return self.visits[len(self.visits) - 1].poi_id

	def add_visit(self, visit):
		self.visits.append(visit)

	def add_photo(self, photo):
		self.photos.append(photo)

	def as_list(self):
		return [x.poi_id for x in self.visits]

	def get_duration(self):
		if self.duration != -1:
			return self.duration
		
		self.duration = 0
		for v in self.visits:
			self.duration += v.duration
		
		return self.duration

	def __eq__(self, other):
		return other is not None and int(self.seq_id) == int(other.seq_id)
	
	def __hash__(self):
		return hash(self.seq_id)

	def __str__(self):
		v = [x.poi_id for x in self.visits]
		return str(v)


class POIQueue:
	def __init__(self, num_pois):
		self.num_pois = num_pois
		self.q = {}
		self.n_q = {}

		for i in range(0, 60):
			self.q[i] = {}
			self.n_q[i] = {}
			for j in range(1, num_pois + 1):
				self.q[i][j] = 0
				self.n_q[i][j] = 0
		
	def add_to_queue(self, sequence, pois):
		total_time = 0
		order = 0

		for visit in sequence.visits:
			visit_duration = visit.duration
			ride_duration = pois[visit.poi_id].ride_duration
			queue_t = visit_duration - ride_duration
			
			if queue_t < 0:
				continue

			#t = int(math.floor(total_time / 3600))
			t = order

			print("t: {},  poi_id: {}".format(t, visit.poi_id))
			print(sequence.seq_id)
			print(total_time)
			self.q[t][visit.poi_id] += queue_t
			self.n_q[t][visit.poi_id] += 1
			total_time += visit_duration
			order += 1

	def  get_queue(self, total_time, poi_id):
		#t = int(math.floor(total_time / 3600))
		t = total_time

		if self.n_q[t][poi_id] == 0:
			return 0

		return self.q[t][poi_id] / self.n_q[t][poi_id]



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

	def get_category(self):
		return self.category[0]


class Photo:
	def __init__(self, poi_taken, time_taken, category):
		self.poi_taken = poi_taken
		self.time_taken = time_taken
		self.category = category


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

running = Instance()