import Image, array, struct, os, base64, zlib, math, logging, argparse

from HurricanObjects import object_info


import xml.etree.ElementTree as ET

class HurricanMap:
    bi_wall	    = 0x000001
    bi_enemy_wall   = 0x000002
    bi_platform	    = 0x000004
    bi_use_light    = 0x000008
    bi_overlap	    = 0x000010
    bi_animate_back = 0x000020
    bi_animate_front= 0x000040
    bi_water 	    = 0x000080
    bi_damage 	    = 0x000100
    bi_conv_l 	    = 0x000200
    bi_conv_r 	    = 0x000400
    bi_turn	    = 0x000800
    bi_destroyable  = 0x001000
    bi_tex_left	    = 0x002000
    bi_overlight    = 0x004000
    bi_swamp	    = 0x008000
    bi_ice	    = 0x010000
    bi_tex_down	    = 0x020000
    bi_waterfall    = 0x040000
    bi_tex_right    = 0x080000

    def __init__(self):
	# index, x, y, flags, difficulty, val1, val2
	self.objects = []
	self.tileset = []
	self.watercolour1 = 0x0033FF66
	self.watercolour2 = 0x0088FF44
	self.powerblock = 0
	self.flashlight = False
	self.static_image = "static_jungle.png"
	self.back_image = "back_jungle.png"
	self.front_image = "front_jungle.png"
	self.clouds_image = "clouds_jungle.bmp"
	self.bgm_level = "JungleBeats.it"
	self.bgm_boss = "boss_robofist.it"
	self.timelimit = 999
	self.scroll_back = True
	
	self.size = (0,0)
	
	self.colours = array.array("I")
	self.flags = array.array("I")
	self.front = array.array("H") # tile * 144 + index + 1
	self.back = array.array("H") # tile * 144 + index + 1

    def setsize(self, size):
	self.size = size
	width, height = self.size
	
	count = width * height
	self.colours.extend([0] * count)
	self.flags.extend([0] * count)
	self.front.extend([0] * count)
	self.back.extend([0] * count)

    def write(self, name):
	f = open(name, "wb")

	# Header
	header = "Hurrican Level File V1.0 (c) 2002 Poke53280 - "
	f.write(struct.pack("<146s24s24s24s26siB", header + "\0", self.static_image + "\0", self.back_image + "\0", self.front_image + "\0", self.clouds_image + "\0", self.timelimit, len(self.tileset)))
	for t in self.tileset:
	    f.write(struct.pack("<16s", t + "\0"))
	for i in range(64-len(self.tileset)):
	    f.write(struct.pack("<16s", "\0"))
	width, height = self.size
	f.write(struct.pack("<3Biii4B", 0, 0, 0, width, height, len(self.objects), self.scroll_back, 0, 0, 0))
	
	# tilemap
	for x in range(width):
	    for y in range(height):
		idx = y * width + x
	
		p1 = 0
		t1 = 0
		front_tile = self.front[idx]
		if front_tile > 0:
		    p1 = (front_tile - 1) / 144
		    t1 = ((front_tile - 1) % 144) + 1
		
		p2 = 0
		t2 = 0
		back_tile = self.back[idx]
		if back_tile > 0:
		    p2 = (back_tile - 1) / 144
		    t2 = ((back_tile - 1) % 144) + 1

		f.write(struct.pack("<BBBBII", p2, p1, t2, t1 , self.colours[idx], self.flags[idx]))

	# objects
	for o in self.objects:
	    f.write(struct.pack("<iiibbHii", o[0], o[1], o[2], o[3], o[4], 0, o[5], o[6]))

	# tail header
	f.write(struct.pack("<30s30si8s8si", self.bgm_level + "\0", self.bgm_boss + "\0", self.powerblock, "%08X" % self.watercolour1, "%08X" % self.watercolour2, self.flashlight))

	f.close()

def getProperties(elem):
    properties = {}
    if elem != None:
	for item in elem:
	    if item.tag == "property":
		name = item.get("name")
		value = item.get("value")
		if value[0] == "#": # hex values
		    value = int(value[1:], 16)
		if "." in name: # property with mask
		    name,mask = name.split(".")
		    try:
			base = int(properties[name])
		    except KeyError:
			base = 0
		    value = int(value)
		    for component in mask[::-1]:
			if component == "a":
			    base &= ~0xFF000000
			    base |= (value & 0xFF) << 24
			    value >>= 8
			elif component == "r":
			    base &= ~0x00FF0000
			    base |= (value & 0xFF) << 16
			    value >>= 8
			elif component == "g":
			    base &= ~0x0000FF00
			    base |= (value & 0xFF) << 8
			    value >>= 8
			elif component == "b":
			    base &= ~0x000000FF
			    base |= (value & 0xFF)
			    value >>= 8
			else:
			    logging.warning("unknown component %s" % component)
		    value = base
		properties[name] = value
    return properties

def getTileset(elem, mapdir, firstgid):
    properties = getProperties(elem.find("properties"))
    image = elem.find("image")
    source = os.path.normpath(os.path.join(mapdir, image.get("source")))
    width = int(image.get("width"))
    height = int(image.get("height"))
    surface = Image.open(source)
    surface = surface.convert("RGBA")
    basename = os.path.basename(source)
    tileset = {}
    rows = height / 20
    cols = width / 20
    for y in range(rows):
	for x in range(cols):
	    opaque = True # all pixel non-transparent
	    empty = True # all pixel fully transparent
	    tile = surface.crop((x*20, y*20, x*20+20, y*20+20))
	    for r,g,b,a in tile.getdata():
		if (r,g,b) == (255,0,255):
		    a = 0
		if a < 255:
		    opaque = False
		if a > 0:
		    empty = False
		if not opaque and not empty:
		    break
	    index = y*cols+x
	    tileset[index + firstgid] = (dict(properties.items()), index, basename, opaque, empty)
    for tile in elem.findall("tile"):
	id = int(tile.get("id"))
	tile_properties = getProperties(tile.find("properties"))
	for key, value in properties.items() + tile_properties.items():
	    tileset[id + firstgid][0][key] = value
    return tileset

def convertMap(inputPath, outputPath):
    logging.info("loading %s..." % inputPath)
    mapDir = os.path.dirname(inputPath)

    tileset = {}
    layers = []

    type_lookup = {}
    for key, value in object_info.items():
    	try:
		type_lookup[value["type"]] = key
	except KeyError:
		pass

    hurricanMap = HurricanMap()
    doc = ET.parse(inputPath)
    
    # process
    root = doc.getroot()
    if root.tag == "map":
    
	width = int(root.get("width"))
	height = int(root.get("height"))
	hurricanMap.setsize((width, height))
	
	if width >= 1024 or height >= 1600:
	    logging.warning("The hurrican runtime is normally limited to a maxium level size of 1024 * 1600")

	for elem in root:
	    if elem.tag == "properties":
		properties = getProperties(elem)
		for key, value in properties.items():
		    if key == "flashlight":
			hurricanMap.flashlight = int(value) != 0
		    elif key == "time_limit":
			hurricanMap.timelimit = int(value)
		    elif key == "power_block":
			hurricanMap.powerblock = int(value)
		    elif key == "bgm_boss":
			hurricanMap.bgm_boss = os.path.basename(os.path.normpath(os.path.join(mapDir, str(value))))
		    elif key == "bgm_level":
			hurricanMap.bgm_level = os.path.basename(os.path.normpath(os.path.join(mapDir, str(value))))
		    elif key == "watercolour1":
			hurricanMap.watercolour1 = int(value)
		    elif key == "watercolour2":
			hurricanMap.watercolour2 = int(value)
		    elif key == "scroll_back":
			hurricanMap.scroll_back = int(value) != 0
		    else:
			logging.warning("unknown property: %s" % key)
	    elif elem.tag == "imagelayer":
		name = elem.get("name")
		image = elem.find("image")
		source = os.path.normpath(os.path.join(mapDir, str(image.get("source"))))
		if name == "clouds":
		    hurricanMap.clouds_image = os.path.basename(source)
		elif name == "static":
		    hurricanMap.static_image = os.path.basename(source)
		elif name == "back":
		    hurricanMap.back_image = os.path.basename(source)
		elif name == "front":
		    hurricanMap.front_image = os.path.basename(source)
		else:
		    logging.warning("unknown image layer: %s" % name)
	    elif elem.tag == "objectgroup":
		for obj in elem:
		    if obj.tag == "object":
			type = obj.get("type")
			x = int(obj.get("x"))
			y = int(obj.get("y"))
		    	object_width = int(obj.get("width", "0"))
		    	object_height = int(obj.get("height", "0"))

			change_light = False
			difficuly = 0
			value1 = 0
			value2 = 0
			properties = getProperties(obj.find("properties"))
			for key, value in properties.items():
			    if key == "change_light":
				change_light = int(value) != 0
			    elif key == "difficulty":
				difficulty = int(value)
			    elif key == "value1":
				value1 = int(value)
			    elif key == "value2":
				value2 = int(value)
			    else:
				logging.warning("unknown property: %s" % key)
			try:
			    type_val = type_lookup[type]
			except KeyError:
			    if type[0] == "#":
				type_val = int(type[1:], 16)
			    elif type.isdigit():
				type_val = int(type)
			    else:
				logging.warning("unknown type: %s" % type)
			if type_val == 149:
			    # generate bridge pieces along the length, add "platform" flags
			    x1 = ((x + 10) / 20) * 20
			    x2 = ((x + object_width + 10) / 20) * 20
			    y1 = ((y + 10) / 20) * 20
			    for i in range((x2 - x1) / 10):
				hurricanMap.objects.append((type_val, x1 + i * 10, y1 - 3, change_light, difficulty, value1, value2))
			    for i in range((x2 - x1) / 20):
				hIndex = (x1 / 20 + i) + (y1 / 20) * width
				hurricanMap.flags[hIndex] |= HurricanMap.bi_platform
			elif type_val == 145:
			    # level exits cover an area, so create several overlapping objects
			    exit_width = max(int(obj.get("width")), 120)
			    exit_height = max(int(obj.get("height")), 120)
			    for i in range((exit_height + 119) / 120):
				for j in range((exit_width + 119) / 120):
				    hurricanMap.objects.append((type_val, x + min(j * 120, exit_width - 120), y + min(i * 120, exit_height - 120), change_light, difficulty, value1, value2))
			elif type_val == 171:
			    # secret, store width and height in value1 and value2
			    value1 = max(object_width, 20)
			    value2 = max(object_height, 20)
			    x += (value1 / 2) - 20
			    y += (value2 / 2) - 20
			    hurricanMap.objects.append((type_val, x, y, change_light, difficulty, value1, value2))
			else:
			    try:
			    	# set position to upper left corner
			    	info = object_info[type_val]
			    	x += (object_width / 2) - (info["xfs"] / 2)
			    	y += object_height - info["yfs"]
			    except KeyError:
			    	pass
			    hurricanMap.objects.append((type_val, x, y, change_light, difficulty, value1, value2))
	    elif elem.tag == "colour":
		# colour layers are additive with saturation
		data = elem.find("data")
		compression = data.get("compression")
		encoding = data.get("encoding")
		if compression == "zlib" and encoding == "base64":
		    buffer = zlib.decompress(base64.b64decode(data.text))
		    colour = [struct.unpack_from("<BBBB", buffer, x * 4) for x in range(len(buffer)/4)]
		    for y in range(height):
			for x in range(width):
			    tIndex = y * width + x
			    (r,g,b,a) = colour[tIndex]
			    col = hurricanMap.colours[tIndex]
			    r = min(((col>>0)&255) + r, 255)
			    g = min(((col>>8)&255) + g, 255)
			    b = min(((col>>16)&255) + b, 255)
			    a = min(((col>>24)&255) + a, 255)
			    hurricanMap.colours[tIndex] = r | (g<<8) | (b<<16) | (a<<24)
		else:
		    logging.error("only compression zlib and encoding base64 are supported")
	    elif elem.tag == "layer":
		properties = getProperties(elem.find("properties"))
		data = elem.find("data")
		compression = data.get("compression")
		encoding = data.get("encoding")
		if compression == "zlib" and encoding == "base64":
		    buffer = zlib.decompress(base64.b64decode(data.text))
		    gids = [struct.unpack_from("<I", buffer, x * 4)[0] for x in range(len(buffer)/4)]
		    layers.append((properties, gids))
		else:
		    loging.error("only compression zlib and encoding base64 are supported")
	    elif elem.tag == "tileset":
		firstgid = int(elem.get("firstgid"))
		source = elem.get("source")
		if source != None:
		    tsxDoc = ET.parse(os.path.normpath(os.path.join(mapDir, source)))
		    tileset = dict(tileset.items() + getTileset(tsxDoc.getroot(), mapDir, firstgid).items())
		else:
		    tileset = dict(tileset.items() + getTileset(elem, mapDir, firstgid).items())
    
    tilesetlist = {}
    for y in range(height):
	for x in range(width):
	    tIndex = y * width + x
	    merged_properties = {}
	    tiles = []
	    for layer_properties, gids in layers:
		index = gids[tIndex]
		if index > 0:
		    tile_props, _, _, opaque, empty = tileset[index]			
		    current_properties = dict(layer_properties.items() + tile_props.items())
		    try:
			visible = int(current_properties["visible"]) != 0
		    except KeyError:
			visible = True
		    if visible:
			if opaque:
			    tiles = [index]
			elif not empty:
			    tiles.append(index)
		    merged_properties = dict(merged_properties.items() + current_properties.items())
	    flags = 0
	    for key,value in merged_properties.items():
		if key == "wall":
		    flags |= HurricanMap.bi_wall
		elif key == "enemy_wall":
		    flags |= HurricanMap.bi_enemy_wall
		elif key == "platform":
		    flags |= HurricanMap.bi_platform
		elif key == "use_light":
		    flags |= HurricanMap.bi_use_light
		elif key == "overlap":
		    flags |= HurricanMap.bi_overlap
		elif key == "animate_back":
		    flags |= HurricanMap.bi_animate_back
		elif key == "animate_front":
		    flags |= HurricanMap.bi_animate_front
		elif key == "damage":
		    flags |= HurricanMap.bi_damage
		elif key == "conv_l":
		    flags |= HurricanMap.bi_conv_l
		elif key == "conv_r":
		    flags |= HurricanMap.bi_conv_r
		elif key == "destroyable":
		    flags |= HurricanMap.bi_destroyable
		elif key == "tex_left":
		    flags |= HurricanMap.bi_tex_left
		elif key == "overlight":
		    flags |= HurricanMap.bi_overlight
		elif key == "swamp":
		    flags |= HurricanMap.bi_swamp
		elif key == "ice":
		    flags |= HurricanMap.bi_ice
		elif key == "tex_down":
		    flags |= HurricanMap.bi_tex_down
		elif key == "waterfall":
		    flags |= HurricanMap.bi_waterfall
		elif key == "tex_right":
		    flags |= HurricanMap.bi_tex_right
	    hurricanMap.flags[tIndex] |= flags

	    if len(tiles) > 0:
		index = tiles[0]
		_, tile_index, basename, _, _ = tileset[index]
		try:
		    tileset_index = tilesetlist[basename]
		except KeyError:
		    tileset_index = len(tilesetlist)
		    tilesetlist[basename] = tileset_index
		hurricanMap.back[tIndex] = (tileset_index * 144 + tile_index) + 1
	    if len(tiles) > 1:
		index = tiles[-1]
		_, tile_index, basename, _, _ = tileset[index]
		try:
		    tileset_index = tilesetlist[basename]
		except KeyError:
		    tileset_index = len(tilesetlist)
		    tilesetlist[basename] = tileset_index
		hurricanMap.front[tIndex] = (tileset_index * 144 + tile_index) + 1
    hurricanMap.tileset = [""] * len(tilesetlist)
    for key,value in tilesetlist.items():
	hurricanMap.tileset[value] = key

    logging.info("writing %s..." % outputPath)
    hurricanMap.write(outputPath)

    logging.info("done.")

def main():
    parser = argparse.ArgumentParser(description="Convert Tiled map into Hurrican map.")
    parser.add_argument("input", help="filename of the map to convert", type=str)
    parser.add_argument("-o", "--output", help="filename for the converted map. The default is the input path with the extension set to .tmx", type=str)
    args = parser.parse_args()

    inputPath = os.path.abspath(args.input)
    if os.path.exists(inputPath):
	if args.output != None:
	    outputPath = os.path.abspath(args.output)
	else:
	    outputPath = os.path.splitext(inputPath)[0] + ".map"
	convertMap(inputPath, outputPath)
    else: 
	logging.error("map %s not found!" % inputPath)

if __name__ == "__main__":
    main()
