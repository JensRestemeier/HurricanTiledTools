import Image, array, struct, os, base64, zlib

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

def main(argv):   
    if len(argv) > 1:
	mapname = os.path.abspath(argv[1])
	if os.path.exists(mapname):
	    mapdir = os.path.dirname(mapname)

	    f = open(mapname, "rb")
	    data = f.read();
	    lv6 = array.array("H", [struct.unpack_from("<H", data, x) for x in range(len(data)/2)])
	    f.close()

	    (worldNum, startx, starty, width, height) = lv6[0:5]

	    f = open(os.path.join(mapdir, "world%i.bl6" % worldNum), "rb")
	    data = f.read();
	    bl6 = array.array("H", [struct.unpack_from("<H", data, x) for x in range(len(data)/2)])
	    f.close()

	    # open tile data to get the size and to convert the first tile to 100% black
	    tilepath = os.path.abspath(os.path.join(mapdir, "world%i.bmp" % worldNum))
	    tilepathpng = os.path.splitext(tilepath)[0] + ".png"
	    tileimage = Image.open(tilepath)
	    tileimage.paste((1,1,1,255), (0,0,32,32))
	    tileimage.save(tilepathpng)

	    filename = os.path.abspath(os.path.splitext(mapname)[0]+".tmx")
	    mapdir = os.path.dirname(filename)

	    mapData = ("map", {"version":"1.0", "orientation":"orthogonal", "width":width, "height":height, "tilewidth":32, "tileheight":32 }, [])

	    firstgid = 1
	    tileset =   ("tileset", {"firstgid":firstgid, "name":os.path.splitext(os.path.basename(tilepathpng))[0], "tilewidth":32, "tileheight":32}, [
		("image", {"source":os.path.relpath(tilepathpng, mapdir), "trans":"000000", "width":tileimage.size[0], "height":tileimage.size[1]}, [])
	    ])
	    tilecount = bl6[0]
	    for i in range(tilecount):
		properties = {}
		val = [bl6[tilecount*j+i+1] for j in range(4)]
		if val[0] == 0:
		    properties["wall"] = 1
		elif val[0] == 1:
		    properties["wall"] = 1
		    properties["animate"] = 1
		elif val[0] == 2:
		    properties["wall"] = 1
		    properties["destroy_shot"] = 1
		elif val[0] == 3:
		    properties["wall"] = 1
		    properties["destroy_walk"] = 1
		elif val[0] == 4:
		    properties["wall"] = 1
		    properties["change_walk"] = 1
		elif val[0] == 5:
		    properties["wall"] = 1
		    properties["visible"] = 0
		elif val[0] == 6:
		    properties["wall"] = 0
		elif val[0] == 7:
		    properties["wall"] = 1
		    properties["damage"] = 1
		elif val[0] == 8:
		    properties["wall"] = 1
		    properties["damage"] = 1
		    properties["animate"] = 1
		elif val[0] == 9:
		    properties["wall"] = 0
		    properties["animate"] = 1
		elif val[0] == 10:
		    properties["wall"] = 0
		    properties["sprite"] = 1
		else:
		    properties["data0"] = val[0]
		properties["data1"] = val[1]
		properties["data2"] = val[2]
		properties["data3"] = val[3]	    
		tile = ("tile", {"id":i}, [
		    ("properties", {}, [
			("property",  {"name":key, "value":value}, []) for key,value in properties.items()
		    ])
		])
		tileset[2].append(tile)
	    mapData[2].append(tileset)
	    firstgid += (tileimage.size[0] / 32) * (tileimage.size[1] / 32)
	    
	    # reuse tileset for attributes...
	    attribute_gid = firstgid
	    tileset = ("tileset", {"firstgid":firstgid, "name":"attributes", "tilewidth":32, "tileheight":32}, [
		("image", {"source":os.path.relpath(tilepathpng, mapdir), "trans":"000000", "width":tileimage.size[0], "height":tileimage.size[1]}, [])
	    ])
	    type = ["cave", "waterfall", "waterpool", "underwater", "wind_right", "wind_left", "storm_right", "storm_left", "river_right", "river_left", "exit_right", "exit_left", "exit_up", "exit_down", "shift_right", "shift_left"]
	    for index,val in enumerate(type):
		tile = ("tile", {"id":index}, [
		    ("properties", {}, [
			("property",  {"name":val, "value":1}, [])
		    ])
		])
		tileset[2].append(tile)
	    mapData[2].append(tileset)
	    firstgid += (tileimage.size[0] / 32) * (tileimage.size[1] / 32)

	    tilemap_parallax = []
	    tilemap_background = []
	    tilemap_foreground = []
	    tilemap_attr = []
	    objects = [{"name":"startpos","x":startx*32+320,"y":starty*32+200}]
	    
	    for y in range(height):
		for x in range(width):
		    val = [lv6[5 + y * width + x + width * height * i] for i in range(6)]
		    if val[0] > 0:
			tilemap_parallax.append(val[0] + 1)
		    else:
			tilemap_parallax.append(0)
	    
		    if val[2] > 0:
			tilemap_foreground.append(val[2] + 1)
		    else:
			tilemap_foreground.append(0)
		    if val[3] == 0:
			tilemap_background.append(0)
			tilemap_attr.append(0)
		    elif val[3] == 1: 
			tilemap_background.append(1)
			tilemap_attr.append(0)
		    else:
			tilemap_background.append(0)
			tilemap_attr.append(val[3] + attribute_gid - 1)
			
		    if val[4] > 0:
			objects.append({"name":"object","x":x*32,"y":y*32+32,"gid":val[4]+1})

	    layer = ("layer", {"name":"parallax", "width":width, "height":height}, [
		("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tilemap_parallax])))])
	    ])
	    mapData[2].append(layer)

	    layer = ("layer", {"name":"background", "width":width, "height":height}, [
		("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tilemap_background])))])
	    ])
	    mapData[2].append(layer)

	    layer = ("layer", {"name":"foreground", "width":width, "height":height}, [
		("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tilemap_foreground])))])
	    ])
	    mapData[2].append(layer)

	    layer = ("layer", {"name":"attr", "width":width, "height":height}, [
		("data", {"encoding":"base64", "compression":"zlib"}, [base64.b64encode(zlib.compress("".join([struct.pack("<I", x) for x in tilemap_attr])))])
	    ])
	    mapData[2].append(layer)

	    objectgroup = ("objectgroup", {"name":"objects", "width":width, "height":height}, [
		("object", obj, []) for obj in objects
	    ])

	    mapData[2].append(objectgroup)

	    f = open(filename, "wt")
	    writeData(f, mapData)
	    f.close()

if __name__ == "__main__":
    import sys
    main(sys.argv)

