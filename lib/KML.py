


class KML:

	def __init__(self):
		self.schemas = []
		self.folders = []

		loose = Folder(self, 'Loose')

	def write_to_file(self, filename='output.kml'):
		out = open(filename, 'w')
		out.write('<?xml version="1.0" encoding="utf-8" ?>\n')
		out.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
		out.write('<Document id="root_doc">\n')

		for schema in self.schemas:
			out.write(str(schema))

		for folder in self.folders:
			out.write(str(folder))


		out.write('</Document></kml>\n')
		out.flush()
		out.close()

	def add_loose_placemark(self, placemark):
		if placemark.schema not in self.schemas:
			self.schemas.append(placemark.schema)

		self.folders[0].append(placemark)

	def add_schema (self, schema):
		self.schemas.append(schema)

	def add_folder (self, folder):
		self.folders.append(folder)
		

class Schema:

	def __init__(self, name, id=""):
		if id == "":
			id = name
		self.name = name
		self.id = id
		self.names = []
		self.datatypes = []

	def add_data (self, name, type):
		self.names.append(name)
		self.datatypes.append(type)

	def __str__ (self):
		out = str.format('<Schema name="{0}" id="{0}">\n',self.name)

		for i in range(len(self.names)):
			out += str.format('  <SimpleField name="{}" type="{}"></SimpleField>\n', self.names[i], self.datatypes[i] )

		out += '</Schema>\n'
		return out


class Placemark(dict):

	def __init__(self, schema, name=""):
		self.schema = schema
		self.name = name

	def put_data(self, key, value):
		self[key] = value

	def put_path(self, path, color="ff0000ff"):
		self.line_path = path
		self.line_color = color

	def __str__(self):
		out = '<Placemark>\n'

		out += str.format('<name>{}</name>', self.name)

		#Set line style for drawing a path
		if hasattr(self, 'line_path'):
			out += str.format('  <Style><LineStyle><color>{}</color></LineStyle></Style>\n', self.line_color )

		#Opening header for text data
		out += str.format('  <ExtendedData><SchemaData schemaUrl="#{}">\n', self.schema.id )

		#Add data blocks
		for name in self.schema.names:
			out += str.format('    <SimpleData name="{}">{}</SimpleData>\n', name, self[name] )

		#Close data section
		out += '  </SchemaData></ExtendedData>\n'

		#Mark the map at the coordinates
		if self.has_key("Latitude") and self.has_key("Longitude"):
			out += str.format('  <Point><coordinates>{},{}</coordinates></Point>\n',self['Longitude'],self['Latitude'])

		#Add coordinates for a drawn path
		if hasattr(self, 'line_path'):
			out += '  <LineString><coordinates>'
			for point in self.line_path:
				out += str(point[1]) + "," + str(point[0]) + " "
			out += '</coordinates></LineString>\n'

		out += '</Placemark>\n'
		return out

class Folder:

	def __init__(self, kml_file, name):
		self.file = kml_file
		self.file.add_folder(self)

		self.name = name

		self.placemarks = []

	def add_placemark(self, placemark):
		if placemark.schema not in self.file.schemas:
			self.file.schemas.append(placemark.schema)
		self.placemarks.append(placemark)

	def __str__ (self):
		out = str.format('<Folder><name>{}</name>\n', self.name)

		for placemark in self.placemarks:
			out += str(placemark)

		out += '</Folder>\n'
		return out

if __name__ == "__main__":
	kml = KML()

	folder = Folder(kml, "Testing")
	
	schema = Schema("ID")
	schema.add_data("VesselName", "string")
	schema.add_data("Time", 	"string")
	schema.add_data("Epoch", 	"int"	)
	schema.add_data("Latitude", 	"float"	)
	schema.add_data("Longitude",	"float" )
	
	ship_point = Placemark(schema)
	ship_point.put_data("VesselName", "Henry")
	ship_point.put_data("Time"	, "2018-06-01 04:34:21")
	ship_point.put_data("Epoch"	, 1527852861)
	ship_point.put_data("Latitude"	, 60.0)
	ship_point.put_data("Longitude"	, -160.0)

	ship_path = Placemark(schema)
	ship_path.put_data("VesselName", "Henry")
	ship_path.put_data("Time"	, "2018-06-01 04:34:21")
	ship_path.put_data("Epoch"	, 1527852861)
	ship_path.put_data("Latitude"	, 60.0)
	ship_path.put_data("Longitude"	, -160.0)
	coords = [(60,-160) , (60,-161) , (61,-170) ]
	ship_path.put_path(coords, "ff00ff0f")
	
	
	folder.add_placemark(ship_point)
	folder.add_placemark(ship_path)
	
	kml.write_to_file("test.kml")









