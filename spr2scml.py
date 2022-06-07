# This converts all animations into a format that can be used with Spriter
import glob, re, os, array, math, argparse
from PIL import Image
import xml.etree.ElementTree as ET

def convertSprites(base_dir, output_dir):
    output_path = os.path.join(output_dir, "hurrican.scml")

    sprite_data = ET.Element("spriter_data", scml_version="1.0", generator="BrashMonkey Spriter", generator_version="r11", pixel_mode="1")

    folder_lookup = {}
    entity_lookup = {}

    recover_alpha = {
        "blitztexture":True,
        "lavamann":True,
        "droneflame":True,
        "Blitzflash1":True,
        "Blitzflash2":True,
        "Blitzflash3":True,
        "Blitzflash4":True,
        "Blitztexture":True,
        "SchussFlamme":True,
        "SchussFlamme2":True,
        "SchussFlamme3":True,
        "SchussFlammeFlare":True,
        "Loading":True,
        "beamsmoke":True,
        "beamsmoke2":True,
        "beamsmoke5":True,
        "drache_smoke":True,
        "evilfunke":True,
        "evilroundsmoke":True,
        "explosion-regular":True,
        "explosion-trace":True,
        "extracollected":True,
        "fireball_smoke":True,
        "flugsacksmoke":True,
        "giantspiderflare":True,
        "grenadeflare":True,
        "kringel":True,
        "laserflame":True,
        "laserfunke":True,
        "lavaflare":True,
        "MINIFLARE":True,
        "pharaosmoke":True,
        "rocketsmoke":True,
        "Blitzstrahl1":True,
        "Blitzstrahl2":True,
        "Blitzstrahl3":True,
        "Blitzstrahl4":True,
        "rocketsmokeblue":True,
        "rocketsmokegreen":True,
        "evilshot":True,
        "evilshot2":True,
        "fetterspinnenlaser":True,
        "explosion-big":True,
        "shield":True,
        "spreadshot_big":True,
        "shockexplosion":True,
        "walker-laser":True,
        "spreadshot":True,
        "spreadshot2":True,
        "spreadshot_big2":True,
        "shotflare":True,
        "snowflush":True,
        "spidershotsmoke":True,
        "stelzlaser":True,
        "turbinesmoke":True,
        "ufolaserflare":True,
        "blitzbeam":True,
        "BRATKLOPSSHOT":True,
        "druckwelle":True,
        "elektropampe":True,
        "evilblitz":True,
        "evilblitz2":True,
        "fettespinneshot":True,
        "fettespinneshot2":True,
        "fireball":True,
        "fireball_big":True,
        "flame":True,
        "golemschuss":True,
        "flamme":True,
        "laser":True,
        "laser2":True,
        "laserbig":True,
        "laserbig2":True,
        "pflanzeschuss":True,
        "pharaolaser":True,
        "powerline":True,
        "rotzshot":True,
        "spidershot":True,
        "spidershot2":True,
        "spiderslow":True,
        "suchschuss2":True,
        "ufolaser":True,
        "bratklopslaser":True,
        "bratklopsshot2":True,
        "skeletor_flame":True,
        "Star":True,
        "Loadingbar":True,
    }

    for file in glob.glob(os.path.join(base_dir, "*.cpp")):
        source_name,_ = os.path.splitext(os.path.basename(file))
        with open(file, "rt") as f:
            data = f.read()
        for m in re.findall(r"\s*(.*)(->|\.)LoadImage\s*\(\s*\"(.*)\",\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\);", data):
            target, _, image, w,h, tw, th, cx, cy = m
            image_name,_ = os.path.splitext(image)
            print (source_name, target, image, w,h, tw, th, cx, cy)
            im = Image.open(os.path.join(base_dir, "data", image))
            cx = int(cx)
            cy = int(cy)
            tw = int(tw)
            th = int(th)

            # fix up transparency:
            if im.mode == "P":
                pal = im.getpalette("RGBA")
                for i in range(len(pal)//4):
                    if (pal[i*4+0], pal[i*4+1], pal[i*4+2]) == (255,0,255):
                        for j in range(4):
                            pal[i*4+j] = 0
                try:
                    transparency = im.info["transparency"]
                    if type(transparency) == int:
                        for j in range(4):
                            pal[transparency*4+j] = 0
                    else:
                        for i,alpha in enumerate(transparency):
                            if alpha == 0:
                                for j in range(4):
                                    pal[i*4+j] = 0
                            else:
                                pal[i*4+3] = alpha
                except KeyError:
                    pass
                im.putpalette(pal, "RGBA")
            else:
                im = im.convert("RGBA")
                data = []
                for col in im.getdata():
                    if (col[0], col[1], col[2]) == (255,0,255):
                        col = (0,0,0,0)
                    data.append(col)
                im.putdata(data)

            # try to recover alpha for pre-multiplied effect textures:
            try:
                fix_alpha = recover_alpha[image_name]
            except KeyError:
                fix_alpha = False
            if fix_alpha:
                im = im.convert("RGBA")
                data = []
                for col in im.getdata():
                    r,g,b,a = col
                    if a == 255:
                        m = max(r,g,b)
                        if m < 255 and m > 0:
                            rf, gf, bf = r/255.0, g/255.0, b/255.0
                            found = False
                            for a in range(m, 256):
                                af = a/255.0
                                # estimate original r,g,b
                                ro = round(min(rf / af, 1.0) * 255.0)
                                go = round(min(gf / af, 1.0) * 255.0)
                                bo = round(min(bf / af, 1.0) * 255.0)

                                # recover alpha-blended r,g,b for verification
                                rt = round(min((ro / 255.0) * af, 1.0) * 255.0)
                                gt = round(min((go / 255.0) * af, 1.0) * 255.0)
                                bt = round(min((bo / 255.0) * af, 1.0) * 255.0)

                                # print ((r,g,b), (rt,gt,bt), (ro, go, bo), a)
                                if (r,g,b) == (rt,gt,bt):
                                    data.append((ro,go,bo,a))
                                    found = True
                                    break
                            if not found:
                                data.append((r,g,b,255))
                        elif m == 0:
                            data.append((0,0,0,0))
                        else:
                            data.append(col)
                    else:
                        data.append(col)
                im.putdata(data)

            outDir = os.path.join(output_dir, source_name)
            os.makedirs(outDir, exist_ok=True)

            try:
                folder = folder_lookup[source_name]
            except KeyError:
                folder_id = len(sprite_data.findall("./folder"))
                folder = ET.SubElement(sprite_data, "folder", id=str(folder_id), name=source_name)
                folder_lookup[source_name] = folder

            try:
                entity = entity_lookup[source_name]
            except KeyError:
                entity = {}
                entity_lookup[source_name] = entity

            # split animaiton info frames:
            frame_count = cx * cy
            if frame_count > 1:
                file_id = len(folder.findall("./file"))
                for y in range(cy):
                    for x in range(cx):
                        frame = im.crop((x * tw, y * th, x*tw+tw, y*th+th))

                        # on the last row we check if we reached an empty frame
                        if x > 0 and y == (cy-1):
                            data=frame.getdata()
                            first = data[0]
                            valid = False
                            for col in data:
                                if col != first:
                                    valid = True
                                    break
                            if not valid:
                                frame_count = y * cx + x
                                break

                        frame_index = y*cx+x
                        image_path = os.path.join(outDir, "%s.%i.png" % (image_name, frame_index))
                        frame.save(image_path)
                        file = ET.SubElement(folder, "file", id=str(file_id + frame_index), name=os.path.relpath(image_path, output_dir), width=str(tw), height=str(th), pivot_x=str(0.5), pivot_y=str(0.0))
                if frame_count > 0:
                    entity[image_name] = (folder_id, file_id, frame_count)
            else:
                image_path = os.path.join(outDir, image_name + ".png")
                im.save(image_path)
                file_id = len(folder.findall("./file"))
                file = ET.SubElement(folder, "file", id=str(file_id), name=os.path.relpath(image_path, output_dir), width=str(tw), height=str(th), pivot_x=str(0.5), pivot_y=str(0.0))
                entity[image_name] = (folder_id, file_id, 1)

    frame_len = 32
    for entity_id, (entity_name, entity_data) in enumerate(entity_lookup.items()):
        entity = ET.SubElement(sprite_data, "entity", id=str(entity_id), name=entity_name)
        for animation_id, (animation_name, animation_data) in enumerate(entity_data.items()):
            folder_id, file_id, frame_count = animation_data
            animation = ET.SubElement(entity, "animation", id=str(animation_id), name=animation_name, interval=str(100), length=str(frame_count * frame_len))
            mainline = ET.SubElement(animation, "mainline")
            for i in range(frame_count):
                key = ET.SubElement(mainline, "key", id=str(i), time=str(i*frame_len))
                object_ref = ET.SubElement(key, "object_ref", id=str(0), timeline=str(0), key=str(i), z_index=str(0))
            timeline = ET.SubElement(animation, "timeline", id=str(0), name=animation_name)
            for i in range(frame_count):
                key = ET.SubElement(timeline, "key", id=str(i), time=str(i*frame_len), curve_type="instant")
                object = ET.SubElement(key, "object", folder=str(folder_id), file=str(file_id + i), x=str(0), y=str(0))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        ET.ElementTree(sprite_data).write(f, encoding='utf-8', xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(description="Convert Hurrican sprites into Spriter scml format.")
    parser.add_argument("input", help="base directory of source code", type=str)
    parser.add_argument("-o", "--output", help="base directory to write the sprites to", type=str)
    args = parser.parse_args()

    if os.path.exists(args.input):
        output_dir = "scml"
        if args.output != None:
            output_dir = args.output

        convertSprites(args.input, output_dir)
    else:
        print ("input path not found")

if __name__ == "__main__":
    main()
