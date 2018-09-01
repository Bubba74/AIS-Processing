import csv	#For parsing AIS.csv input
import time	#Timing and ship time time_struct manipulations
import sys	#For sys.stdout.write continuous printing

#For KML Output
from fastkml.kml import KML, Document, Folder, Placemark, ExtendedData, Data
from fastkml import Style, IconStyle, LineStyle
from pygeoif.geometry import Point, LineString, GeometryCollection

import random	#For creating unique colors for ship paths
import math	#Lat/lon distance calculations for ships



EARTH_RADIUS 	= 6.371e6	#meters
MAX_BOAT_SPEED  = 228.0 / 3600 	#nautical miles per second (of fastest boat)
MAX_BOAT_SPEED	= 100.0 / 3600  #slightly slower

BLIP_ICON = "https://cdn4.iconfinder.com/data/icons/6x16-free-application-icons/16/Target.png"
#BLIP_ICON = "http://asset-a.soupcdn.com/asset/0897/8622_a476_32-square.png"

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
	global kml_file, kml_doc
	global ship_schema, blip_schema, approach_schema
	global paths_folder, blips_folder, approaches_folder

	kml_file = KML() # Root KML object
	kml_doc = Document(name="AIS_Output")
	kml_file.append(kml_doc)
	
	paths_folder = Folder(name="Ship Paths")
	paths_folder.visibility = 0
	blips_folder = Folder(name="Ship Blips")
	blips_folder.visibility = 0
	approaches_folder = Folder(name="Ship Approaches")

	#Append folders to kml doc
	kml_doc.append(paths_folder)
	kml_doc.append(blips_folder)
	kml_doc.append(approaches_folder)


def get_random_abgr_color ():
	color = "ff"
	for i in range(6):
		rng = random.randint(48, 63) #0-9 == 48-57    a-f == 97,102
		if rng > 57: #Map 58 to 97
			rng += 39
		color += chr(rng)
	return color


def draw_ship_path (ship):
	abgr = get_random_abgr_color()

	blip_folder = Folder( name="Blips: "+ship.name)
	blip_folder.visibility = 0

	# Text box info
	data = ExtendedData ()
	data.elements.append( Data(None, 'VesselName'	, ship.name) )
	data.elements.append( Data(None, 'Time'		, ship.get_strf_time(0)) )
	data.elements.append( Data(None, 'Epoch'	, str(ship.get_epoch(0))) )
	data.elements.append( Data(None, 'Latitude'	, str(ship.get_lat(0))) )
	data.elements.append( Data(None, 'Longitude'	, str(ship.get_lon(0))) )

	# Geometry
	coords = [( ship.get_lon(i) , ship.get_lat(i) ) for i in range(ship.len())]
	path_line = LineString(coordinates=coords)
	start_point = Point(ship.get_lon(0), ship.get_lat(0))
	geo_combo = GeometryCollection( ([start_point , path_line]) )

	# Style
	icon = IconStyle( scale=0.5, icon_href=BLIP_ICON )
	linestyle = LineStyle (color=abgr)
	style = Style( styles=[icon, linestyle] )
	
	path = Placemark(name=ship.name)	# Create placemark
	path.visibility = 1			# Don't show all paths by default
	path.extended_data = data		# Add descriptive data for the ship
	path.geometry = geo_combo		# Attach geometry: start point + line path
	path.append_style(style)		# Decrease size of icon


	paths_folder.append(path)

	#Add points along path
	for i in range(ship.len()):
		#Set the color of the icon based on the color of the path
		#Scale=0.2, icon=BLIP_ICON, color=color

		data = ExtendedData ()
		data.elements.append( Data(None, "Time"		, ship.get_strf_time(i) ) )
		data.elements.append( Data(None, "Latitude"	, str(ship.get_lat(i)) ) )
		data.elements.append( Data(None, "Longitude"	, str(ship.get_lon(i)) ) )
		
		blip = Placemark()
		blip.append_style(Style(styles=[IconStyle(color=abgr, scale=0.2, icon_href=BLIP_ICON)]))
		blip.geometry = Point( ship.get_lon(i) , ship.get_lat(i) )
		blip.extended_data = data

		blip_folder.append(blip)
	blips_folder.append(blip_folder)

def draw_ship_approach (approach):
	global approaches_folder

	identifier = approach[0]
	ship1 = identifier[0]
	index1 = identifier[1]
	ship2 = identifier[2]
	index2 = identifier[3]

	approach_folder = Folder( name=str.format('{} - {}',ship1.name,ship2.name) )
	approaches_folder.append(approach_folder)

	# --  Marker for first ship -- #
	data = ExtendedData()
	data.elements.append(Data(None, 'VesselName'	, ship1.name))
	data.elements.append(Data(None, 'Time' 		, ship1.get_strf_time(index1)))
	data.elements.append(Data(None, 'Latitude'	, str(ship1.get_lat(index1))))
	data.elements.append(Data(None, 'Longitude'	, str(ship1.get_lon(index1))))
	
	point1 = Point( ship1.get_lon(index1) , ship1.get_lat(index1) )
	p1 = Placemark(name=ship1.name)
	p1.extended_data = data
	p1.append_style(Style(styles=[IconStyle(scale=0.3, color="ffffffff")]))
	p1.geometry = point1

	# --  Marker for second ship -- #
	data = ExtendedData()
	data.elements.append(Data(None, 'VesselName'	, ship2.name))
	data.elements.append(Data(None, 'Time' 		, ship2.get_strf_time(index2)))
	data.elements.append(Data(None, 'Latitude'	, str(ship2.get_lat(index2))))
	data.elements.append(Data(None, 'Longitude'	, str(ship2.get_lon(index2))))
	
	point2 = Point( ship2.get_lon(index2) , ship2.get_lat(index2) )
	p2 = Placemark(name=ship2.name)
	p2.extended_data = data
	p2.append_style(Style(styles=[IconStyle(scale=0.3, color="ffffffff")]))
	p2.geometry = point2

	# --  Marker for third ship -- #
	#Paired lat/lon coordinates denoting connection between ships
	coords = [ (ship1.get_lon(index1), ship1.get_lat(index1)) , (ship2.get_lon(index2),ship2.get_lat(index2)) ]


	data = ExtendedData()
	data.elements.append( Data(None,'Distance'	, str.format('{:.2f}nm' , approach[1][0]) ) )
	data.elements.append( Data(None,'Vessel1'	, ship1.name ) )
	data.elements.append( Data(None,'Vessel2'	, ship2.name ) )
	data.elements.append( Data(None,'Time1'		, ship1.get_strf_time(index1) ) )
	data.elements.append( Data(None,'Time2'		, ship2.get_strf_time(index2) ) )

	p_approach = Placemark( name=str.format('{}nm', approach[1][0]) )
	p_approach.extended_data = data
	p_approach.append_style(Style( styles=[IconStyle(scale=0.4, color="ff0000ff"), LineStyle(width=2)] ))
	p_approach.geometry = LineString(coords)

	approach_folder.append(p1)
	approach_folder.append(p2)
	approach_folder.append(p_approach)
	

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

	def jump_sec (self, index, seconds):
		#Constrain output to less than self.len()
		if index+1 >= self.len():
			return self.len()-1

		start = self.get_epoch(index)
		while self.get_epoch(index+1) - start < seconds:
			index += 1
			if index == self.len()-1:
				break
		return index

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
	
	sys.stdout.write("Comparing ships " + ship1.name + " and " + ship2.name)
	sys.stdout.flush()
	#print ship1
	#print ship2
	
	start_time = time.time() # Start clock on comparing ships
	while index1 < ship1.len() and index2 < ship2.len():
		proximity = 3000
		#Seek until ship timestamps are within 5 minute
		while True:
			epoch1 = ship1.get_epoch(index1)
			epoch2 = ship2.get_epoch(index2)
			if abs( epoch1 - epoch2 ) < proximity:
				#print "Found similar timestamps"
				#print "Ship1: Index: " + str(index1) + " -  " + ship1.get_strf_time(index1)
				#print "Ship2: Index: " + str(index2) + " -  " + ship2.get_strf_time(index2)
				
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

			#Closest the ships will get in time
			if index1 >= ship1.len():
				break
			if index2 >= ship2.len():
				break

		if index1 >= ship1.len() or index2 >= ship2.len():
			break

		distance = 25 #Shortest distance between vessels at time
		identifier = (ship1,index1,ship2,index2) #Reference for source of approach
		#Scan through points measuring distances
		while True:
			dist = ship1.distance_nm(index1,ship2,index2,speed=True)
			if dist < distance:
				distance = dist
				identifier = (ship1, index1, ship2, index2)

			#print str(dist)+'nm'
			if dist > 30: #If the boats are more than 30 nm away
				gap = dist - 20
				time_jump = gap/MAX_BOAT_SPEED/2
				#print "Jumping forward "+str(int(time_jump))+" seconds"
				index1 = ship1.jump_sec(index1, time_jump)
				index2 = ship2.jump_sec(index2, time_jump)
			
			epoch1 = ship1.get_epoch(index1)
			epoch2 = ship2.get_epoch(index2)
			if epoch1 < epoch2:
				index1 += 1
			else:
				index2 += 1

			#If either ship moved more than 50 minutes into the future
			end_of_path 	= index1 >= ship1.len() or index2 >= ship2.len()
			time_jump = False
			if not end_of_path: #Be careful of get_epoch out_of_bounds
				time_jump	= (ship1.get_epoch(index1)-epoch1 > 3000) or (ship2.get_epoch(index2)-epoch2 > 3000)

			if end_of_path or time_jump:
				if distance < 25:
					locations = ( distance, ship1.get_lat(identifier[1]), ship1.get_lon(identifier[1]), ship2.get_lat(identifier[3]), ship2.get_lon(identifier[3]) )
					approaches.append ( (identifier, locations) )
					distance = 25
				#end_of_path -- Ship with earliest timestamps has reached the end of its path
				#time_jump   -- The ships are no longer time-synced
				break

	end_time = time.time() # Stop clock on comparing ships
	print str.format("	 {:.2f} seconds", end_time-start_time)
			
	for approach in approaches:
		print str.format( "-------Approach between {}:{} and {}:{}", approach[0][0].name, approach[0][1], approach[0][2].name, approach[0][3] )
		print str.format( "({},{}) and ({},{}) == {:.2f}nm", approach[1][1], approach[1][2], approach[1][3], approach[1][4], approach[1][0] )
		draw_ship_approach(approach)
			

#Setup KML output
kml_setup()

ships = []


filename = "../AIS_Data.csv"
if len(sys.argv)>1:
	filename = sys.argv[1]

csv_file = open(filename)
reader = csv.reader(csv_file, delimiter=',')

unnamed_index = 0

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

	if name == "":
		name = "Unnamed_"+str(unnamed_index)
		unnamed_index += 1

	position = Position(raw_time, lat, lon)
	get_ship(ships, name).add_point(position)

	index += 1
	if index % block_size == 0:
		print_progress(time_start, index)
		if index // block_size >= 10:
			block_size *= 10
csv_file.close() # Free data file resources

print_progress(time_start, index)

for ship in ships:
	print ship
	print

shipc = len(ships)
pathc = sum([ships[i].len() for i in range(len(ships))])

print str.format("{} vessels : {} markers", shipc, pathc)
print "\n"

for i in range(len(ships)):
	for j in range(i+1, len(ships)):
		compare_ships(ships[i],ships[j])

for ship in ships:
	draw_ship_path(ship)

fout = open('AIS_Processing.kml', 'w')
fout.write(kml_file.to_string(prettyprint=True))
fout.close()


print str.format("Program finished in {:.2f} seconds.", time.time()-time_start)
