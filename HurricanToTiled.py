import struct, os, array, math, zlib, base64, random, argparse, logging
import xml.etree.ElementTree as ET
from PIL import Image

from HurricanObjects import object_info

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
    for i in range(len(searchPath)-1, -1, -1):
        curPath = os.path.join(searchPath[i], s)
        if os.path.exists(curPath):
            return os.path.normpath(curPath)
    return None

def reduce(s):
    zero = s.find(b"\0")
    if zero >= 0:
        return s[0:zero].decode()
    else:
        return s.decode()

def convertMap(inputPath, outputPath):
    logging.info("loading %s..." % inputPath)
    mapDir = os.path.dirname(inputPath)
    outputDir = os.path.dirname(outputPath)
    os.makedirs(outputDir, exist_ok=True)
    searchPath.append(mapDir)

    f = open(inputPath, "rb")

    # Header
    (header, static_image, back_image, front_image, clouds_image, timelimit, tileset_count) = struct.unpack("<146s24s24s24s26siB", f.read(249))
    # print (header, static_image, back_image, front_image, clouds_image, timelimit, tileset_count) 
    header = reduce(header)
    
    tileset_paths = []
    for i in range(tileset_count):
        texturePath = findFile(reduce(f.read(16)))
        logging.info("loading %s..." % texturePath)
        im = Image.open(texturePath)
        name,ext = os.path.splitext(os.path.basename(texturePath))
        if ext.lower() == ".bmp":
            texturePath = os.path.abspath(os.path.join(outputDir, name + ".png"))
            if not os.path.exists(texturePath):
                im.save(texturePath)
        tileset_paths.append((texturePath, len(im.getbands()) < 4))

    f.seek((64-tileset_count) * 16 + 3, os.SEEK_CUR)
    
    # map
    (width, height, object_count, scrollback, stuff2, stuff3, stuff4) = struct.unpack("<iii4B", f.read(16))
    map = []
    for r in range(width):
        col = []
        for c in range(height):
            col.append(struct.unpack("<BBBBII", f.read(12))) # tileset_background, tileset_foreground, index1, index2, colour, flags
        map.append(col)

    # objects
    objects = []
    for o in range(object_count):
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
    tilemap_vcolors = []

    tileset_attr = []
    tileset_count = [0] * 20
    for i in range(20):
            tileset_attr.append([])

    tileset_vcolors = []
    vcolor_map = {}
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
                try:
                    idx = vcolor_map[col]
                except KeyError:
                    idx = len(tileset_vcolors)
                    tileset_vcolors.append(col)
                    vcolor_map[col] = idx
                tilemap_vcolors.append(idx)

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
        
        mapData = ET.Element("map", {"version":"1.0", "orientation":"orthogonal", "width":str(width), "height":str(height), "tilewidth":str(20), "tileheight":str(20)})
        properties = ET.SubElement(mapData, "properties")
        #property = ET.SubElement(properties, "property", {"name":"name","value":name}) # export name. makes it possible to keep several variations of a level.
        #property = ET.SubElement(properties, "property", {"name":"level","value":name}) # level pack to export into
        property = ET.SubElement(properties, "property", {"name":"bgm_level","type":"file","value":os.path.relpath(findFile(bgm_level), outputDir)})
        property = ET.SubElement(properties, "property", {"name":"bgm_boss","type":"file","value":os.path.relpath(findFile(bgm_boss), outputDir)})
        property = ET.SubElement(properties, "property", {"name":"time_limit","type":"int","value":str(timelimit)})
        property = ET.SubElement(properties, "property", {"name":"power_block","type":"int","value":str(powerblock)})
        property = ET.SubElement(properties, "property", {"name":"flashlight","type":"bool", "value":"true" if flashlight!=0 else "false"})
        property = ET.SubElement(properties, "property", {"name":"watercolour1.a","type":"int","value":str((col1>>0)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour1.b","type":"int","value":str((col1>>8)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour1.g","type":"int","value":str((col1>>16)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour1.r","type":"int","value":str((col1>>24)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour2.a","type":"int","value":str((col2>>0)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour2.b","type":"int","value":str((col2>>8)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour2.g","type":"int","value":str((col2>>16)&255)})
        property = ET.SubElement(properties, "property", {"name":"watercolour2.r","type":"int","value":str((col2>>24)&255)})
        property = ET.SubElement(properties, "property", {"name":"scroll_back","type":"int","value":str(scrollback)})

        firstgid = 1
        for path,trans in tileset_paths:
            # install: copy tileset into target dirctory when exporting level
            name,_ = os.path.splitext(os.path.basename(path))
            tileset = ET.SubElement(mapData, "tileset", {"firstgid":str(firstgid), "name":name, "tilewidth":str(20), "tileheight":str(20)})
            im = Image.open(path)
            image = ET.SubElement(tileset, "image", {"source":os.path.relpath(path, outputDir), "width":str(im.width), "height":str(im.height)})
            if trans:
                image.set("trans", "ff00ff")
            if name.lower() == "s_arrow":
                # add tile animation for arrows:
                for y in range(2):
                    for x in range(8):
                        tile = ET.SubElement(tileset, "tile", id=str(y * 12 + x))
                        animation = ET.SubElement(tile, "animation")
                        for i in range(4):
                            frame = ET.SubElement(animation, "frame", tileid=str(y*12+x+i*36), duration=str(100))

            firstgid += 144

        attr_icons_path = os.path.abspath("attribute_icons.tsx")
        tileset = ET.SubElement(mapData, "tileset", {"firstgid":str(firstgid), "source":os.path.relpath(attr_icons_path, outputDir), "tilewidth":str(20), "tileheight":str(20)})
        for i in range(20):
            for j in range(len(tileset_attr[i])):
                    if tileset_attr[i][j] > 0:
                            tileset_attr[i][j] += firstgid - 1
        firstgid += 36
        
        vcolors_path = os.path.join(outputDir, "vcolors.png")
        cols = 64
        rows = (len(tileset_vcolors) + (cols-1)) // cols
        im = Image.new("RGBA", (cols * 20, rows * 20))
        for i in range(len(tileset_vcolors)):
            r = i // cols
            c = i % cols
            for y in range(20):
                for x in range(20):
                    im.putpixel((x+c*20,y+r*20), tileset_vcolors[i])
        im.save(vcolors_path)

        vcolor_start = firstgid
        tileset = ET.SubElement(mapData, "tileset", {"firstgid":str(firstgid), "name":"colors", "tilewidth":str(20), "tileheight":str(20)})
        image = ET.SubElement(tileset, "image", {"source":os.path.relpath(vcolors_path, outputDir), "width":str(im.width), "height":str(im.height)})

        firstgid += rows * cols

        imagepath = findFile(reduce(clouds_image))
        im = Image.open(imagepath)
        imagelayer = ET.SubElement(mapData, "imagelayer", {"name":"clouds", "width":str(im.width), "height":str(im.height)})
        image = ET.SubElement(imagelayer, "image", {"source":os.path.relpath(imagepath, outputDir)})

        imagepath = findFile(reduce(static_image))
        im = Image.open(imagepath)
        imagelayer = ET.SubElement(mapData, "imagelayer", {"name":"static", "width":str(im.width), "height":str(im.height)})
        image = ET.SubElement(imagelayer, "image", {"source":os.path.relpath(imagepath, outputDir)})

        imagepath = findFile(reduce(back_image))
        im = Image.open(imagepath)
        imagelayer = ET.SubElement(mapData, "imagelayer", {"name":"back", "width":str(im.width), "height":str(im.height)})
        image = ET.SubElement(imagelayer, "image", {"source":os.path.relpath(imagepath, outputDir)})

        imagepath = findFile(reduce(front_image))
        im = Image.open(imagepath)
        imagelayer = ET.SubElement(mapData, "imagelayer", {"name":"front", "width":str(im.width), "height":str(im.height)})
        image = ET.SubElement(imagelayer, "image", {"source":os.path.relpath(imagepath, outputDir)})
        
        layer = ET.SubElement(mapData, "layer", {"name":"background", "width":str(width), "height":str(height)})
        data = ET.SubElement(layer, "data", {"encoding":"base64", "compression":"zlib"})
        data.text = base64.b64encode(zlib.compress(b"".join([struct.pack("<I", x) for x in tileset_background]))).decode()
        
        layer = ET.SubElement(mapData, "layer", {"name":"foreground", "width":str(width), "height":str(height)})
        data = ET.SubElement(layer, "data", {"encoding":"base64", "compression":"zlib"})
        data.text = base64.b64encode(zlib.compress(b"".join([struct.pack("<I", x) for x in tileset_foreground]))).decode()

        layer = ET.SubElement(mapData, "layer", {"name":"attr_colour", "width":str(width), "height":str(height), "opacity":"0.5"})
        data = ET.SubElement(layer, "data", {"encoding":"csv"})
        data.text = ",".join([str(vcolor_start+x) for x in tilemap_vcolors])
        properties = ET.SubElement(layer, "properties")
        property = ET.SubElement(properties, "property", name="colour", type="bool", value="true")

        for i in range(20):
            if tileset_count[i] > 0:
                layer = ET.SubElement(mapData, "layer", {"name":"attr_" + attr_name[i], "width":str(width), "height":str(height), "opacity":"0.5"})
                data = ET.SubElement(layer, "data", {"encoding":"base64", "compression":"zlib"})
                data.text = base64.b64encode(zlib.compress(b"".join([struct.pack("<I", x) for x in tileset_attr[i]]))).decode()

        # create bridge
        bridgeObjects = []
        objectgroup = ET.SubElement(mapData, "objectgroup", {"name":"objects", "width":str(width), "height":str(height)})
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
                object = ET.SubElement(objectgroup, "object", {"name":n,"type":t,"x":str(o[1]),"y":str(o[2]),"width":str(width),"height":str(height)})
                properties = ET.SubElement(object, "properties")
                property = ET.SubElement(properties, "property", {"name":"change_light","value":str(o[3])})
                property = ET.SubElement(properties, "property", {"name":"difficulty","value":str(o[4])})
                property = ET.SubElement(properties, "property", {"name":"value1","value":str(o[6])})
                property = ET.SubElement(properties, "property", {"name":"value2","value":str(o[7])})
                if o[0] == 171: 
                    # secret
                    object.set("x", str(int(object.get("x", "0")) - (o[6]/2) - 20))
                    object.set("y", str(int(object.get("y", "0")) - (o[7]/2) - 20))
                    object.set("width", str(o[6]))
                    object.set("height", str(o[7]))
                

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
            b = sorted(b, key=lambda key: key[1])
        
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
            object = ET.SubElement(objectgroup, "object", {"name":str(o["name"]),"type":str(o["type"]),"x":str(o["x"]),"y":str(o["y"]),"width":str(o["width"])})
            properties = ET.SubElement(object, "properties")
            property = ET.SubElement(properties, "property", {"name":"change_light","value":str(o["change_light"])})
            property = ET.SubElement(properties, "property", {"name":"difficulty","value":str(o["difficulty"])})
            property = ET.SubElement(properties, "property", {"name":"value1","value":str(o["value1"])})
            property = ET.SubElement(properties, "property", {"name":"value2","value":str(o["value2"])})

        logging.info("writing %s..." % outputPath)
        os.makedirs(os.path.dirname(outputPath), exist_ok=True)
        with open(outputPath, 'wb') as f:
            ET.ElementTree(mapData).write(f, encoding='utf-8', xml_declaration=True)

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
