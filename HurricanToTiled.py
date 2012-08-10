import struct, os, array, math, zlib, base64, random, Image, argparse, logging

from HurricanObjects import object_info

def writeData(f, node, indent=0):
    if indent >= 0:
	f.write(" " * indent)
    f.write("<%s" % node[0])
    items = node[1].items()
    items.sort()
    for key, value in items:
	f.write(" %s=\"%s\"" % (key, value))
    if len(node[2]) > 0:
	f.write(">")
	doIndent = indent >= 0
	for item in node[2]:
	    if type(item) != tuple:
		doIndent = False
	if doIndent:
	    f.write("\n")
	    for item in node[2]:
		writeData(f, item, indent + 1)
	else:
	    x = []
	    for item in node[2]:
		if type(item) == tuple:
		    if len(x) > 0:
			f.write(" ".join(x))
			x = []
		    writeData(f, item, -1)
		else:
		    x.append(str(item))
	    if len(x) > 0:
		f.write(" ".join(x))
		x = []
	if indent >= 0 and doIndent:
	    f.write(" " * indent)
	f.write("</%s>" % node[0])
    else:
	f.write("/>")
    if indent >= 0:
	f.write("\n")

searchPath = []

def findHurricanExe(searchDir):
    hurripathTxt = os.path.join(searchDir, "hurripath.txt")
    if os.path.exists(hurripathTxt):
	f = open(hurripathTxt, "r")
	foundDir = f.read()
	f.close()
	return foundDir
    else:
	hurricanExe = os.path.join(searchDir, "hurrican.exe")
	if os.path.exists(hurricanExe):
	    return searchDir
	else:
	    parentDir = os.path.dirname(searchDir)
	    if parentDir != searchDir:
		return findHurricanExe(parentDir)
	    else:
		return None

def findHurricanData(mapDir):
    hurricanExeDir = findHurricanExe(mapDir)
    if hurricanExeDir == None:
	hurricanExeDir = findHurricanExe(os.getcwd())
    if hurricanExeDir == None:
	return None
    else:
	return os.path.join(hurricanExeDir, "data")

def findFile(s):
    for i in xrange(len(searchPath)-1, -1, -1):
	curPath = os.path.join(searchPath[i], s)
	if os.path.exists(curPath):
	    return os.path.normpath(curPath)
    return None

def reduce(s):
    zero = s.find("\0")
    if zero >= 0:
	return s[0:zero]
    else:
	return s

def convertMap(inputPath, outputPath):
    logging.info("loading %s..." % inputPath)
    mapDir = os.path.dirname(inputPath)
    searchPath.append(mapDir)

    f = open(inputPath, "rb")

    # Header
    (header, static_image, back_image, front_image, clouds_image, timelimit, tileset_count) = struct.unpack("<146s24s24s24s26siB", f.read(249))
    # print (header, static_image, back_image, front_image, clouds_image, timelimit, tileset_count) 
    header = reduce(header)
    
    tileset_paths = []
    for i in xrange(tileset_count):
	texturePath = findFile(reduce(f.read(16)))
	logging.info("loading %s..." % texturePath)
	surface = Image.open(texturePath)
	name,ext = os.path.splitext(os.path.basename(texturePath))
	if ext.lower() == ".bmp":
	    texturePath = os.path.abspath(name + ".png")
	    if not os.path.exists(texturePath):
		surface.save(texturePath)
	tileset_paths.append((texturePath, len(surface.getbands()) < 4))

    f.seek((64-tileset_count) * 16 + 3, os.SEEK_CUR)
    
    # map
    (width, height, object_count, scrollback, stuff2, stuff3, stuff4) = struct.unpack("<iii4B", f.read(16))
    map = []
    for r in xrange(width):
	col = []
	for c in xrange(height):
	    col.append(struct.unpack("<BBBBII", f.read(12))) # tileset_background, tileset_foreground, index1, index2, colour, flags
	map.append(col)

    # objects
    objects = []
    for o in xrange(object_count):
	objects.append(struct.unpack("<iiibbHii", f.read(24))) # index, x, y, flags, difficulty, ?, val1, val2

    # difficulty: 0: easy, 1: medium, 2: hard

    (bgm_level, bgm_boss, powerblock, col1, col2, flashlight) = struct.unpack("<30s30si8s8si", f.read(84))

    bgm_level = reduce(bgm_level) # bgm level
    bgm_boss = reduce(bgm_boss) # bgm boss
    col1 = int(reduce(col1), 16) # water1
    col2 = int(reduce(col2), 16) # water2

    f.close()

    tileset_background = []
    tileset_foreground = []
    tileset_vcolours = []

    tileset_attr = []
    tileset_count = [0] * 20
    for i in range(20):
	    tileset_attr.append([])

    for y in range(height):
	    for x in range(width):
		tile = map[x][y]
		if tile[2] > 0:
		    tileset_background.append(tile[0] * 144 + tile[2])
		else:
		    tileset_background.append(0)
		if tile[3] > 0:
		    tileset_foreground.append(tile[1] * 144 + tile[3])
		else:
		    tileset_foreground.append(0)
	    
		col = ((tile[4]>>0)&255,(tile[4]>>8)&255,(tile[4]>>16)&255,(tile[4]>>24)&255)
		tileset_vcolours.append(col)

		for i in range(20):
			if tile[5] & (1<<i):
			    tileset_attr[i].append(i+1)
			    tileset_count[i] += 1
			else:
			    tileset_attr[i].append(0)

    if True:
	# todo: project file with list of levels 

	attr_name = [
	    "wall", #  0x000001
	    "enemy_wall", #  0x000002
	    "platform", #  0x000004
	    "use_light", #  0x000008
	    "overlap", #  0x000010
	    "animate_back", #  0x000020
	    "animate_front", #  0x000040
	    "water", #  0x000080
	    "damage", #  0x000100
	    "conv_l", #  0x000200
	    "conv_r", #  0x000400
	    "turn", #  0x000800
	    "destroyable", #  0x001000
	    "tex_left", #  0x002000
	    "overlight", #  0x004000
	    "swamp", #  0x008000
	    "ice",   #  0x010000
	    "tex_down", #  0x020000
	    "waterfall", #  0x040000
	    "tex_right"] #  0x080000
	
	
	name,_ = os.path.splitext(os.path.basename(inputPath))
	filename = os.path.abspath(name+".tmx")
	mapdir = os.path.dirname(filename)

	mapData = ("map", {"version":"1.0", "orientation":"orthogonal", "width":width, "height":height, "tilewidth":20, "tileheight":20 }, [
	    ("properties", {}, [
		#("property", {"name":"name","value":name}, []), # export name. makes it possible to keep several variations of a level.
		#("property", {"name":"level","value":name}, []), # level pack to export into
		("property", {"name":"bgm_level","value":os.path.relpath(findFile(reduce(bgm_level)), mapdir)}, []),
		("property", {"name":"bgm_boss","value":os.path.relpath(findFile(reduce(bgm_boss)), mapdir)}, []),
		("property", {"name":"time_limit","value":timelimit}, []),
		("property", {"name":"power_block","value":powerblock}, []),
		("property", {"name":"flashlight","value":flashlight}, []),
		("property", {"name":"watercolour1.a","value":(col1>>0)&255}, []),
		("property", {"name":"watercolour1.b","value":(col1>>8)&255}, []),
		("property", {"name":"watercolour1.g","value":(col1>>16)&255}, []),
		("property", {"name":"watercolour1.r","value":(col1>>24)&255}, []),
		("property", {"name":"watercolour2.a","value":(col2>>0)&255}, []),
		("property", {"name":"watercolour2.b","value":(col2>>8)&255}, []),
		("property", {"name":"watercolour2.g","value":(col2>>16)&255}, []),
		("property", {"name":"watercolour2.r","value":(col2>>24)&255}, []),
		("property", {"name":"scroll_back","value":scrollback}, [])
	    ])
	])
	firstgid = 1
	for path,trans in tileset_paths:
	    # install: copy tileset into target dirctory when exporting level
	    image = ("image", {"source":os.path.relpath(path, mapdir), "width":256, "height":256}, [])
	    if trans:
		image[1]["trans"] = "ff00ff"
	    tileset = ("tileset", {"firstgid":firstgid, "name":os.path.splitext(os.path.basename(path))[0], "tilewidth":20, "tileheight":20}, [
		image
	    ])
	    firstgid += 144
	    mapData[2].append(tileset)

	attr_icons_path = os.path.abspath("attribute_icons.tsx")
	tileset = ("tileset", {"firstgid":firstgid, "source":os.path.relpath(attr_icons_path, mapdir)}, [])
	for i in range(20):
	    for j in range(len(tileset_attr[i])):
		    if tileset_attr[i][j] > 0:
			    tileset_attr[i][j] += firstgid - 1
	firstgid += 36
	mapData[2].append(tileset)
	
	imagepath = findFile(reduce(clouds_image))
	image = Image.open(imagepath)
	imagelayer = ("imagelayer", {"name":"clouds", "width":image.size[0], "height":image.size[1]}, [
	    ("image", {"source":os.path.relpath(imagepath, mapdir)}, [])
	])
	mapData[2].append(imagelayer)

	imagepath = findFile(reduce(static_image))
	image = Image.open(imagepath)
	imagelayer = ("imagelayer", {"name":"static", "width":image.size[0], "height":image.size[1]}, [
	    ("image", {"source":os.path.relpath(imagepath, mapdir)}, [])
	])
	mapData[2].append(imagelayer)

	imagepath = findFile(reduce(back_image))
	image = Image.open(imagepath)
	imagelayer = ("imagelayer", {"name":"back", "width":image.size[0], "height":image.size[1]}, [
	    ("image", {"source":os.path.relpath(imagepath, mapdir)}, [])
	])
	mapData[2].append(imagelayer)

	imagepath = findFile(reduce(front_image))
	image = Image.open(imagepath)
	imagelayer = ("imagelayer", {"name":"front", "width":image.size[0], "height":image.size[1]}, [
	    ("image", {"source":os.path.relpath(imagepath, mapdir)}, [])
	])
	mapData[2].append(imagelayer)
	
	layer = ("layer", {"name":"background", "width":width, "height":height}, [
	    ("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tileset_background])))])
	])
	mapData[2].append(layer)
	layer = ("layer", {"name":"foreground", "width":width, "height":height}, [
	    ("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tileset_foreground])))])
	])
	mapData[2].append(layer)
	layer = ("colour", {"name":"attr_colour", "width":width, "height":height, "opacity":0.5}, [
	    ("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<BBBB ", *x) for x in tileset_vcolours])))])
	])
	mapData[2].append(layer)

	for i in range(20):
	    if tileset_count[i] > 0:
		layer = ("layer", {"name":"attr_" + attr_name[i], "width":width, "height":height, "opacity":0.5}, [
		    ("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tileset_attr[i]])))])
		])
		mapData[2].append(layer)

	bridgeObjects = []
	objectgroup = ("objectgroup", {"name":"objects", "width":1000, "height":1000}, [])
	for o in objects:
	    if o[0] == 149:
		    bridgeObjects.append(o)
	    else:
	    	try:
	    		width = object_info[o[0]]["xfs"]
	    		height = object_info[o[0]]["yfs"]
	    	except KeyError:
	    		width = 0
	    		height = 0
		try:
			n = object_info[o[0]]["name"]
			t = object_info[o[0]]["type"]
		except KeyError:
			n = "Unknown %i" % o[0]
			t = "%i" % o[0]
		object = ("object", {"name":n,"type":t,"x":o[1],"y":o[2],"width":width,"height":height}, [
		    ("properties", {}, [
			("property", {"name":"change_light","value":o[3]}, []),
			("property", {"name":"difficulty","value":o[4]}, []),
			("property", {"name":"value1","value":o[6]}, []),
			("property", {"name":"value2","value":o[7]}, []),
		    ])
		])
		if o[0] == 171: 
		    # secret
		    object[1]["x"] -= (o[6]/2) - 20
		    object[1]["y"] -= (o[7]/2) - 20
		    object[1]["width"] = o[6]
		    object[1]["height"] = o[7]
		objectgroup[2].append(object)

	# group bridges by Y
	bridgeGroups = {}
	for o in bridgeObjects:
	    try:
		    bridgeGroups[o[2]].append(o)
	    except:
		    bridgeGroups[o[2]] = [o]
	
	# join bridges together
	bridges = []
	for b in bridgeGroups.values():
	    # sort by x
	    b.sort(lambda x, y: cmp(x[1],y[1]))
	
	    bridge = None
	    for o in b:
		    if bridge != None:
			    if bridge["x"] > o[1] or bridge["x"] + bridge["width"] + 10 < o[1] or bridge["change_light"] != o[3] or bridge["difficulty"] != o[4] or bridge["value1"] != o[6] or bridge["value2"] != o[7]:
				    bridges.append(bridge)
				    bridge = None
			    else:
				    bridge["width"] = o[1] - bridge["x"] + 10
		    if bridge == None:
			    bridge = {
				    "name":"Bridge %i" % len(bridges),
				    "type":object_info[149]["type"],
				    "x":o[1],
				    "y":o[2],
				    "change_light":o[3],
				    "difficulty":o[4],
				    "value1":o[6],
				    "value2":o[7],
				    "width":10
			    }
	    if bridge != None:
		bridges.append(bridge)

	for o in bridges:
	    object = ("object", {"name":o["name"],"type":o["type"],"x":o["x"],"y":o["y"],"width":o["width"]}, [
		("properties", {}, [
		    ("property", {"name":"change_light","value":o["change_light"]}, []),
		    ("property", {"name":"difficulty","value":o["difficulty"]}, []),
		    ("property", {"name":"value1","value":o["value1"]}, []),
		    ("property", {"name":"value2","value":o["value2"]}, []),
		])
	    ])
	    objectgroup[2].append(object)
	mapData[2].append(objectgroup)

	logging.info("writing %s..." % outputPath)
	f = open(outputPath, "wt")
	writeData(f, mapData)
	f.close()

    logging.info("done.")

def main():
    parser = argparse.ArgumentParser(description="Convert Hurrican map into Tiled map.")
    parser.add_argument("input", help="filename of the map to convert", type=str)
    parser.add_argument("-S", "--searrchpath", help="addtitional search path to look for tiles and images referenced in the map", type=str, nargs="+")
    parser.add_argument("-o", "--output", help="filename for the converted map. The default is the input path with the extension set to .tmx", type=str)
    args = parser.parse_args()
    
    inputPath = os.path.abspath(args.input)
    if os.path.exists(inputPath):
	mapDir = os.path.dirname(inputPath)
	
	if args.searrchpath != None:
	    for path in args.searrchpath:
		searchPath.append(os.path.abspath(path))
	
	hurricanDataPath = findHurricanData(mapDir)
	if hurricanDataPath != None:
	    searchPath.append(hurricanDataPath)
	else:
	    logging.warning("Data dir not found! Let's hope your tilesets are in the same directory as the map!")

	if args.output != None:
	    outputPath = os.path.abspath(args.output)
	else:
	    outputPath = os.path.splitext(inputPath)[0] + ".tmx"

	convertMap(inputPath, outputPath)

    else: 
	logging.error("map %s not found!" % inputPath)

if __name__ == "__main__":
    main()
