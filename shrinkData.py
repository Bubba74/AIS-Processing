import time


start = time.clock()

lines = 0

with open('./ais_input.csv') as r, open('./slimmed_ais_input.csv','w') as w:
	for line in r:
		segs = line.split(',')
		status = segs[11]
		name = segs[7]
		if status == 'at anchor' or name == '' or name == 'VesselName':
			continue
		blip_time, lat, lon = segs[1:4]
		w.write( ','.join((blip_time,name,lat,lon)) + '\n' )
		lines += 1


end = time.clock()

print "Processed {} lines in {} seconds.".format(lines, end-start)
	
