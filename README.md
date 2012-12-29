HurricanTiledTools
==================
Work in progress, not ready for primetime... But it is an option for advanced users who don't want to (or can't) run the 
original editor in a Windows VM. As always, make regular backups of important data, especially before running new and untested
scripts.

General
-------
These are python scripts and data files to create levels for [Hurrican](http://turrican.gamevoice.de/hurrican_site/) with [Tiled](http://www.mapeditor.org/). Tiled uses an XML formatted file with the 
extension .tmx, and Hurrican uses a binary file with the extension .map.

You can experiment with my [forked version of Tiled](http://github.com/JensRestemeier/tiled) that supports colour layers to edit the lighting in a Hurrican level.

These scripts requires [Python 2.7](http://www.python.org/getit/releases/2.7/) (don't download a newer version unless you're able to fix any language or api differences!), and the [python imaging library](http://www.pythonware.com/products/pil/). 

You'll need access to the data from the game. On windows you should follow the [instructions for the original editor](http://www.turrican.gamevoice.de/hurrican_site/forum/showthread.php?id=265)
and unrar the data file. In case the forum post disappears, rename "hurrican.dat" into "hurrican.rar", and use the password "kochello". 
On MacOS this data is included in the application bundle and you can simply copy it to a convenient location.

HurricanToTiled.py
------------------
This is a tool to convert a Hurrican format map for Tiled. You can use a map created by this tool as a template for creating your own levels.

```bash
$ python2.7 HurricanToTiled.py <map_file> -o <tmx_file> [-S <search_path_for_tiles>]
```

If for some reason the converter has trouble finding the tilesets you can use the -S option to add a search path.

TiledToHurrican.py
------------------
This produces a Hurrican level from Tiled. As an example you should look at a file produced by HurricanToTiled.py.

```bash
$ python2.7 TiledToHurrican.py <tmx_file> -o <map_file>
```

Generally the rules are:
- layer names don't matter, except for image layers. Image layers are used to set the scrolling backdrop layers.
- you can have as many attribute layers as you want, and you can have any kind of attribute in a layer. For example it makes sense to combine mutually exclusive attributes in a single layer. The HurricanToTiled.py script just creates a new layer for each attribute to simplify the code.
- you can have as many colour layers as you want. Colour values are added together.
- you can have as many tile layers as you want, but the engine only supports two overlapping tiles. The code ignores all empty tiles and tiles below a 100% opaque tile. 
- if you create new tilesets you're still bound to the sizes used by Hurrican. (20x20 pixel tiles in a 256x256 pixel image.) It'll be your responsibility to copy new tilesets into the map directory.
- normal objects are placed so that the centre of the baseline in the editor is at the centre of the baseline in the game. The easiest way to handle this is to just copy objects from a converted level into your level.
- there is special handling for bridges, level exits and secrets. For bridges you can place an object with height 0 and however wide you want, and the script will create the bridge data for you. For exits you can just mark the area of the exit in your map, and the script will set up objects to cover that area for you. And for secrets it will copy the object width and height into the value1 and value2 properties.

The header information from Hurrican is translated into map properties:
* bgm_level - music to play during the level
* bgm_boss - music to play during boss fights
* time_limit - time limit
* power_block - which power block design to use
* flashlight - limited visibiliy
* watercolour1.r - water colour 1 red component
* watercolour1.g - water colour 1 green component
* watercolour1.b - water colour 1 blue component
* watercolour1.a - water colour 1 alpha component
* watercolour2.r - water colour 2 red component
* watercolour2.g - water colour 2 green component
* watercolour2.b - water colour 2 blue component
* watercolour2.a - water colour 2 alpha component
* scroll_back - enable scrolling for the backdrop layers

Again, you can use one of the converted levels as an example.

T2002ToTiled.py
---------------
This converts a [T2002](http://www.pekaro.de/t2002.html) level to Tiled format. This was mostly a test for me, and I probably won't be maintaining it. Feel free to fork and modify it.

```bash
$ python2.7 T2002ToTiled.py <mapname>
```

This creates a tmx file in the same directory and converts the .bmp file with the tiles into a .png file.

publish.py
----------
Beginnings of a publishing script to package a level into a zip file and create an RSS feed that can be picked up from a Hurrican launcher.

```bash
$ python2.7 publish.py <rss_feed> <level_dir_or_level_zip>
```

The script expects a manifest.xml file in the level dir, that is a stripped-down item entry for the rss feed (i.e. minus the automatically generated parts). If no manifest exists a template will be generated, and if no rss feed exists a template for that will be generated as well. The script can publish a zip file as well, but then it can't create a template manifest.xml if it doesn't exist. Both the RSS feed and the manifest.xml template should be edited before publishing, because you need to change the descriptions, names and urls. You can change the guid as well if you don't want a random one, but it should stay unchanged after you publish a level. Future version will use the guid when merging entries from several separate RSS feeds.
With a bit of extra free time I could probably add some kind of wx or Tk UI for this.

You will then have to upload the resulting .rss and .zip files to your web space. 

The inspiration for this is the [Appcast](http://connectedflow.com/appcasting/) system used for example by [Sparkle](http://sparkle.andymatuschak.org/) on MacOS. A launcher can use this to automtially install
and update levels for Hurrican. My Hurrican launcher (to be released "real soon now") will use this together with the text
based format that the Windows version was going to use.

