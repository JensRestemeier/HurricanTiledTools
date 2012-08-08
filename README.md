HurricanTiledTools
==================
Work in progress, not ready for primetime...

General
-------
These are python scripts and data files to create levels for Hurrican with Tiled.

These scripts requires Python 2.7 ( http://www.python.org/getit/releases/2.7/ , don't download a newer version unless you're able to fix any language or api differences!), and the python imaging library ( http://www.pythonware.com/products/pil/ ). 

You'll need access to the data from the game. On windows you should follow the instructions for the original editor and unrar the data file. On MacOS this data is included in the application bundle and you can simply copy it to a convenient location.

HurricanToTiled.py
------------------
This is a tool to convert a Hurrican format map for Tiled. You can use a map created by this tool as a template for creating your own levels.

It is run from the command line like this: 
    $ python2.7 HurricanToTiled.py PATH_TO_HURRICAN_DATA/cave.map -o cave.tmx
and it produces a tmx file in the same directory. If for some reason the converter has trouble finding the tilesets you can use the -S option to add a search path.

TiledToHurrican.py
------------------
This produces a Hurrican level from Tiled. As an example you should look at a file produced by HurricanToTiled.py.
Generally the rules are:
- layer names don't matter, except for image layers. Image layers are used to set the scrolling backdrop layers.
- you can have as many attribute layers as you want, and you can have any kind of attribute in a layer. For example it makes sense to combine mutually exclusive attributes in a single layer. The HurricanToTiled.py script just creates a new layer for each attribute to simplify the code.
- you can have as many colour layers as you want. Colour values are added together.
- you can have as many tile layers as you want, but the engine only supports two overlapping tiles. The code ignores all empty tiles and tiles below a 100% opaque tile. 
- if you create new tilesets you're still bound to the sizes used by Hurrican. (20x20 pixel tiles in a 256x256 pixel image.) It'll be your responsibility to copy new tilesets into the map directory.
- normal objects are placed so that the centre of the baseline in the editor is at the centre of the baseline in the game. The easiest way to handle this is to just copy objects from a converted level into your level.
- there is special handling for bridges, level exits and secrets. For bridges you can place an object with height 0 and however wide you want, and the script will create the bridge data for you. For exits you can just mark the area of the exit in your map, and the script will set up objects to cover that area for you. And for secrets it will copy the object width and height into the value1 and value2 properties.

The header information from Hurrican is translated into map properties:
    bgm_level - music to play during the level
    bgm_boss - music to play during boss fights
    time_limit - time limit
    power_block - which power block design to use.
    flashlight - limited visibiliy
    watercolour1.r - water colour 1 red component
    watercolour1.g - water colour 1 green component
    watercolour1.b - water colour 1 blue component
    watercolour1.a - water colou1 1 alpha component
    watercolour2.r - water colour 2 red component
    watercolour2.g - water colour 2 green component
    watercolour2.b - water colour 2 blue component
    watercolour2.a - water colour 2 alpha component
    scroll_back - enable scrolling for the backgdrop layers.
Again, use one of the converted levels as an example.

T2002ToTiled.py
---------------
This converts a T2002 level to Tiled format. This was mostly a test for me, and I probably won't be maintaining it. Feel free to fork and modify it.

