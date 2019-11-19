import instance
import montecarlo

data = instance.running
mcts = montecarlo.MCTS(iteration_limit=1000)

def intersection(lst1, lst2): 
    return set(lst1).intersection(set(lst2))

def union(lst1, lst2): 
    return (list(set(lst1) | set(lst2)))

for theme in data.theme_parks:
	recall_val = 0
	precision_val = 0
	it_n = 0
	for user in data.users[theme].values():
		#print(user.user_id)
		if len(user.sequences) < 2:
			continue

		for s in user.sequences:
			if len(s.visits) < 2:
				continue

			initial_state = s.get_initial_poi()
			final_state = s.get_final_poi()
			budget = s.get_duration()
			distance_matrix = data.distance_matrix[theme]
			pois = data.pois[theme]
			queue_time = data.queues[theme]
			#print(s)
			#print(len(user.sequences))

			itinerary = mcts.search(initial_state, final_state, budget, distance_matrix, pois, user, queue_time, s)
			print("Sequence {}".format(s))
			print("Itinerary {}".format(itinerary))
			print("")

			#it_n += 1

			if itinerary is not None:
				it_n += 1
				recall_val += len(intersection(itinerary, s.as_list())) / len(s.as_list())
				precision_val += len(intersection(itinerary, s.as_list())) / len(itinerary)
		
	print(recall_val / it_n)
	print(precision_val / it_n)