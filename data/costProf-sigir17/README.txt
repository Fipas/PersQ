==================================================================
Attraction/POI Cost-Profit Table for Theme Parks
==================================================================

Dataset Information: 
This dataset comprises various cost-profit tables (for five theme parks) that indicate the cost (based on distance) required to travel from one attraction/point-of-interest (POI) to another attraction/POI, and the resulting profit (based on popularity) gained from reaching that POI. These cost-profit tables are derived from the "Theme Park Attraction Visits Dataset" dataset, i.e., the various "userVisits-{themeParkName}.csv" files from "data-ijcai15.zip".

File Description:
There are a total of five files, each named "costProfCat-{themeParkName}POI-all.csv", where each row indicated a link from one attraction/POI to another and the associated cost (distance), profit (popularity), theme (category), lat/lon coordinates and attraction/ride duration.

The cost-profit table for each city is stored in a single csv file that contains the following columns/fields:
 - from: poiID of the starting POI.
 - to: poiID of the destination POI.
 - cost: distance (metres) between the starting POI (from) to the destination POI (to).
 - profit: popularity of the destination POI (to), based on number of POI visits
 - theme: category of the POI (e.g., Park, Museum, Cultural, etc).
 - rideDuration: duration (seconds) to complete the attraction/ride.

------------------------------------------------------------------
References / Citations
------------------------------------------------------------------
If you use this dataset, please cite the following paper:
 - Kwan Hui Lim, Jeffrey Chan, Shanika Karunasekera and Christopher Leckie. "Personalized Itinerary Recommendation with Queuing Time Awareness". Proceedings of the 40th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR'17). Pg 325-334. Aug 2017.

The corresponding bibtex for this paper is:
 @INPROCEEDINGS { lim-sigir17,
	AUTHOR = {Kwan Hui Lim and Jeffrey Chan and Shanika Karunasekera and Christopher Leckie},
	TITLE = {Personalized Itinerary Recommendation with Queuing Time Awareness},
	BOOKTITLE = {Proceedings of the 40th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR'17)},
	PAGES = {325-334},
	YEAR = {2017}
 }
