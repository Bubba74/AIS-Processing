import csv
import time

import random
import math

import lib.KML as KML

EARTH_RADIUS = 6.371e6

def parseTime(raw_csv_time):
	try:
		year 	= int(raw_csv_time[0:4])
		month 	= int(raw_csv_time[5:7])
		day 	= int(raw_csv_time[8:10])
		hour	= int(raw_csv_time[11:13])
		minute	= int(raw_csv_time[14:16])
		second	= int(raw_csv_time[17:19])
		#   print str.format("Year: {} Month: {} Day: {}  {}:{}:{}", year, month, day, hour, minute, second)
		return time.struct_time((year, month, day, hour, minute, second, 1, 1, -1)) #Returns a generic time struct
	except Exception as e:
		print e
		print "Errored trying to parse time: "+raw_csv_time

def print_progress(time_start, index):
	print str.format("Read through {} rows in {} seconds",index,time.time()-time_start)

def pretty_time (gm_time):
	return time.strftime("%Y-%m-%d %H:%M:%S", gm_time)

		
def kml_setup():
	global kml_output, ship_schema, ship_paths_folder
	kml_output = KML.KML()
	
	ship_schema = KML.Schema("Ship")
	ship_schema.add_data("VesselName",	"string")
	ship_schema.add_data("Time",	"string")
	ship_schema.add_data("Epoch",	"int")
	ship_schema.add_data("Latitude",	"float")
	ship_schema.add_data("Longitude",	"float")
	
	
	ship_paths_folder = KML.Folder(kml_output, "Ship Paths")


def get_random_abgr_color ():
	color = "ff"
	for i in range(6):
		rng = random.randint(48, 63) #0-9 == 48-57    a-f == 97,102
		if rng > 57: #Map 58 to 97
			rng += 39
		color += chr(rng)
	return color


def draw_ship_path (ship):
	global ship_paths_folder

	placemark = KML.Placemark(ship_schema, ship.name)
	placemark.put_data('VesselName'	, ship.name)
	placemark.put_data('Time'	, ship.get_strf_time(0))
	placemark.put_data('Epoch'	, ship.get_epoch(0))
	placemark.put_data('Latitude'	, ship.get_lat(0))
	placemark.put_data('Longitude'	, ship.get_lon(0))

	coords = [( ship.get_lat(i) , ship.get_lon(i) ) for i in range(ship.len())]
	placemark.put_path( coords, get_random_abgr_color() )

	ship_paths_folder.add_placemark(placemark)
	

class Position:
	def __init__(self, time, lat, lon):
		self.lat	= float(lat)
		self.lon	= float(lon)
		self.time	= parseTime(time)
	def __str__(self):
		return str.format("Pos {} {} {}", pretty_time(self.time), self.lat, self.lon)

class ShipPath:
	def __init__(self, ship_name):
		self.name = ship_name 	#VesselName
		self.path = [] 		#List of Position points
	def __str__(self):
		txt = str.format("--{}  Path Length: {}\n", self.name, len(self.path))
		txt += "Start: " + str(self.path[0])+"\n"
		txt += "End:   " + str(self.path[-1])+"\n"
		return txt
	def add_point(self, position):
		for i in range(len(self.path)-1,-1,-1):	#Count backward
			if self.path[i].time < position.time:
				self.path.insert(i+1, position)
				return
		self.path.insert(0, position)
	def full_output(self):
		txt = str.format("--{}  Path Length: {}\n", self.name, len(self.path))
		for pos in self.path:
			txt += str(pos)+"\n"
		return txt

	def len(self):
		return len(self.path)
	def get_lat(self, index):
		return self.path[index].lat
	def get_lon(self, index):
		return self.path[index].lon
	def get_time(self, index):
		return self.path[index].time
	def get_epoch(self, index):
		return time.mktime(self.get_time(index))
	def get_strf_time(self, index):
		return pretty_time(self.path[index].time)

	def distance_nm(self, index1, ship2, index2, speed=False):
		lat1 = math.radians(self.get_lat(index1))
		lon1 = math.radians(self.get_lon(index1))
		lat2 = math.radians(ship2.get_lat(index2))
		lon2 = math.radians(ship2.get_lon(index2))
		if speed:
			#Equirectangular Approximation
        		x = (lon2-lon1) * math.cos((lat1+lat2)/2)
        		y = (lat2-lat1)
        		d = math.sqrt(x*x + y*y) / (2*math.pi) * 360 * 60
        		return d
		else:
			#Spherical Law-of-Cosines
        		d = math.acos( math.sin(lat1)*math.sin(lat2) + math.cos(lat1)*math.cos(lat2) * math.cos(lon2-lon1) );
			d /= (2*math.pi) #Divide by 2pi radians for proportional covered of circle
			d *= 360 * 60	 #One nautical is one minute-sweep of earth: 360d * 60m in 2pirad
        		return d


def get_ship(ships, name):
	shipc = len(ships)
	#for i in range(shipc):
		#if ships[i].name == name:
			#return i
	for ship in ships:
		if ship.name == name:
			return ship
	new_ship = ShipPath(name)
	ships.append(new_ship)
	#return shipc
	return new_ship



def compare_ships(ship1, ship2):
	approaches = []


	#Start with first ship at first position
	index1 = 0
	index2 = 0
	
	print "Comparing ships " + ship1.name + " and " + ship2.name
	print ship1
	print ship2
	
	start_time = time.time() # Start clock on comparing ships
	while index1 < ship1.len() and index2 < ship2.len():
		proximity = 3000
		#Seek until ship timestamps are within 5 minute
		while True:
			epoch1 = ship1.get_epoch(index1)
			epoch2 = ship2.get_epoch(index2)
			if abs( epoch1 - epoch2 ) < proximity:
				print "Found similar timestamps"
				print "Ship1: Index: " + str(index1) + " -  " + ship1.get_strf_time(index1)
				print "Ship2: Index: " + str(index2) + " -  " + ship2.get_strf_time(index2)
				
				debug = False
				if debug:
					print "      Ship1 Time                        Ship2 Time"
					for i in range(-30,30):
						try:
							print str(index1+i)+": "+ship1.get_strf_time(index1+i)  +  "\t"+str(index2+i)+": "+ship2.get_strf_time(index2+i)
						except IndexOutOfBoundsException as e:
							print e
							print "Seek back-forward extends beyond array bounds"
				break
			else:
				if epoch1 < epoch2:
					index1 += 1
				else:
					index2 += 1
			if index1 >= ship1.len() or index2 >= ship2.len():
				#Closest the ships will get in time
				break

		distance = 1000000000 #Shortest distance between vessels at time
		identifier = (ship1,index1,ship2,index2) #Reference for source of approach
		#Scan through points measuring distances
		while True:
			dist = ship1.distance_nm(index1,ship2,index2,speed=True)
			if dist < distance:
				distance = dist
				identifier = (ship1, index1, ship2, index2)
			
			epoch1 = ship1.get_epoch(index1)
			epoch2 = ship2.get_epoch(index2)
			if epoch1 < epoch2:
				index1 += 1
			else:
				index2 += 1

			#If either ship moved more than 50 minutes into the future
			end_of_path 	= index1 >= ship1.len() or index2 >= ship2.len()
			if not end_of_path: #Be careful of get_epoch out_of_bounds
				time_jump	= (ship1.get_epoch(index1)-epoch1 > 3000) or (ship2.get_epoch(index2)-epoch2 > 3000)

			if end_of_path or time_jump:
				locations = ( distance, ship1.get_lat(identifier[1]), ship1.get_lon(identifier[1]), ship2.get_lat(identifier[3]), ship2.get_lon(identifier[3]) )
				approaches.append ( (identifier, locations) )
				distance = 1000000000

			if index1 >= ship1.len() or index2 >= ship2.len():
				#Closest the ships will get in time
				break

	end_time = time.time() # Stop clock on comparing ships
	print str.format("Comparison took {:.2f} seconds", end_time-start_time)
			
	for approach in approaches:
		print str.format( "-------Approach between {}:{} and {}:{}", approach[0][0].name, approach[0][1], approach[0][2].name, approach[0][3] )
		print str.format( "({},{}) and ({},{}) == {:.2f}nm", approach[1][1], approach[1][2], approach[1][3], approach[1][4], approach[1][0] )
			

#Setup KML output
kml_setup()

ships = []


csv_file = open('../resources/AIS_Data.csv')
reader = csv.reader(csv_file, delimiter=',')

time_start = time.time()
index = 0
block_size = 100
for row in reader:
	if index == 0:
		index += 1
		continue

	#Disregard stationary points
	status = row[11]
	if status == "at anchor":
		continue

	name = row[7]
	raw_time = row[1]
	lat = row[2]
	lon = row[3]

	position = Position(raw_time, lat, lon)
	get_ship(ships, name).add_point(position)

	index += 1
	if index % block_size == 0:
		print_progress(time_start, index)
		if index // block_size >= 10:
			block_size *= 10

print_progress(time_start, index)

for ship in ships:
	print ship
	print

shipc = len(ships)
pathc = sum([ships[i].len() for i in range(len(ships))])

print str.format("{} vessels : {} markers", shipc, pathc)
print "\n"

compare_ships(ships[3],ships[6])

for ship in ships:
	draw_ship_path(ship)

kml_output.write_to_file('AIS_Processing.kml')
csv_file.close()
