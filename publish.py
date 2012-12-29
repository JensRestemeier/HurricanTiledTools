# script to publish a level
import urlparse, urllib, datetime, os.path, hashlib, sys, getpass, uuid, zipfile
import xml.etree.ElementTree as ET

# usage:
# python2.7 publish.py <rss_feed> <level_dir>
# The script expects a manifest.xml file in the level dir, that is a stripped-down item entry for the rss feed (i.e. minus the automatically generated parts). If no manifest exists a template will be generated,
# and if no rss feed exists a template for that will be generated as well.
# Both should be edited before publishing. You need to change the descriptions, names and urls. You can change the guid as well if you don't want a random one, but it should stay unchanged after you publish a
# level. 

# You will then have to upload the resulting .rss and .zip files to your web space.

RFC822format = "%a, %d %b %Y %H:%M:%S +0000"

# elementtree should really get a built-in pretty-print
def indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main(*argv):
    utcnow = datetime.datetime.utcnow().strftime(RFC822format)

    rssPath = os.path.abspath(argv[1])
    levelPath = os.path.abspath(argv[2])

    ET.register_namespace("media", "http://search.yahoo.com/mrss/") # requires Python2.7. Sorry.

    # check if we need to publish a directory or a zip file
    if os.path.isdir(levelPath):
	# level pack is a directory
    
	# minimal sanity check to detect a hurrican level. I could probably check that all levels referenced in levellist and all textures are present.
	if not os.path.exists(os.path.join(levelPath, "levellist.dat")):
	    print "Not a hurrican level at %s" % levelPath
	    return

	manifestPath = os.path.join(levelPath, "manifest.xml")
		
	# process manifest or create template
	dirty = False
	if os.path.exists(manifestPath):
	    print "Reading manifest %s ..." % os.path.basename(manifestPath)
	    item = ET.parse(manifestPath).getroot()
	else:
	    print "Creating manifest %s ..." % os.path.basename(manifestPath)
	    item = ET.Element("item")
	    dirty = True
	title = item.find("title")
	if title == None:
	    title = ET.SubElement(item, "title").text = "name of your level"  
	    # title for level base
	    dirty = True
	link = item.find("link")
	if link == None:
	    link = ET.SubElement(item, "link").text = "http://link.to.your.website/#level_description"  
	    # link to further information about your level
	    dirty = True
	description = item.find("description")
	if description == None:
	    description = ET.SubElement(item, "description").text = "short Description of your level" 
	    # link to further information about your level
	    dirty = True
	credit = item.find("{http://search.yahoo.com/mrss/}credit")
	if credit == None:
	    credit = ET.SubElement(item, "{http://search.yahoo.com/mrss/}credit",  role="author").text = getpass.getuser() 
	    # Your name. You probably want to change it to something more different from your login name.
	    dirty = True
	guid = item.find("guid")
	if guid == None:
	    guid = ET.SubElement(item, "guid").text = uuid.uuid4().urn 
	    # This is assigned once and should not change over the lifetime of a level. 
	    # If you don't want a random guid you can change to something else, but it must be unique! You shouldn't change it after publishing a level to the world, because it may confuse downloaders!
	    dirty = True
	enclosure = item.find("enclosure")
	if enclosure == None:
	    zipPath = levelPath + ".zip"
	    zipName = os.path.basename(zipPath)
	    enclosure = ET.SubElement(item, "enclosure",  type="application/x-hurrican-level", url=urlparse.urljoin("http://link.to.your.website/", zipName))  
	    # url of where you'll upload the zip file of the level to. You're free to rename the zip file.
	    dirty = True
	else:
	    enclosure.set("type", "application/x-hurrican-level")
	    zipRemote = urllib.unquote(urlparse.urlparse(enclosure.get("url")).path)
	    zipName = os.path.basename(zipRemote)
	    zipPath = os.path.join(os.path.dirname(levelPath), zipName);
	if dirty:
	    print "Writing manifest %s ..." % os.path.basename(manifestPath)
	    print "You need to modify it before publishing it."
	    indent(item) # not really required, but nice for debugging
	    tree = ET.ElementTree(item)
	    tree.write(manifestPath, encoding="utf-8", xml_declaration=True)

	# create zip file
	print "Creating zip file %s ..." % os.path.basename(zipPath)
	if os.path.exists(zipPath):
	    os.rename(zipPath, zipPath + "~")
	zip = zipfile.ZipFile(zipPath, "w", zipfile.ZIP_DEFLATED, True)
	for f in os.listdir(levelPath):
	    if f[0] != ".": # exclude hidden files, mostly SCM or .DS_Store files.
		zip.write(os.path.join(levelPath, f), f)
	zip.close()
    else:
	# level pack is a zip file
	zipPath = levelPath
	print "Opening zip %s ..." % zipPath
	zip = zipfile.ZipFile(zipPath)
	try:
	    zip.getinfo("levellist.dat")
	except KeyError:
	    print "the archive doesn't seem to contain a hurrican level"
	    return
	# we assume that the manifest is mostly correct. It would be possible to write one back into the zip, but then the user
	# would have to unpack the zip for verification/correction.
	print "Reading manifest %s ..." % "manifest.xml"
	f = zip.open("manifest.xml")
	item = ET.parse(f).getroot()
	f.close()
	enclosure = item.find("enclosure")
	guid = item.find("guid")
	print "closing zip %s ..." % zipPath
	zip.close()

    # get hash digest and length:
    print "Calculating sha-1 hash ..."
    f = open(zipPath, "rb")
    data = f.read()
    f.close()
    sha1 = hashlib.sha1(data).hexdigest()
    
    # store in item description
    enclosure.set("length", str(len(data)))
    hash = item.find("{http://search.yahoo.com/mrss/}hash")
    if hash == None:
	hash = ET.SubElement(item, "{http://search.yahoo.com/mrss/}hash", algo="sha-1").text = sha1
    else:
	hash.set("algo", "sha-1")
	hash.text = sha1

    pubDate = item.find("pubDate")
    if pubDate == None:
	pubDate = ET.SubElement(item, "pubDate").text = utcnow
    else:
	pubDate.text = utcnow
    
    # process rss feed or create template
    # The channel header is ediable, but items may be replaced.
    if os.path.exists(rssPath):
	print "Reading feed %s ..." % os.path.basename(rssPath)
	rss = ET.parse(rssPath).getroot()
    else:
	print "Creating feed %s ..." % os.path.basename(rssPath)
	print "You need to modify it before publishing it."
	rss = ET.Element("rss", version="2.0")
    channel = rss.find("channel")
    if channel == None:
	channel = ET.SubElement(rss, "channel")
    title = channel.find("title")
    if title == None:
	title = ET.SubElement(channel, "title").text = "name of your feed" 
	# title for your level feed. Maybe something like "Jonny's cool levels".
    link = channel.find("link")
    if link == None:
	link = ET.SubElement(channel, "link").text = "http://link.to.your.website/" 
	# link to website with further information about your levels.
    description = channel.find("description")
    if description == None:
	description = ET.SubElement(channel, "description").text = "description of your feed" 
	# a short description of your level feed. What about "Cool levels for Hurrican!!!"?
    lastBuildDate = channel.find("lastBuildDate")
    ttl = channel.find("ttl")
    if ttl == None:
	ttl = ET.SubElement(channel, "ttl").text = "%i" % (7 * 24 * 60) 
	# time in minutes until the next check
	# this is not actually checked by the hurrican launcher at the moment, but could be used to cut down traffic to the rss feed in the future.

    # update/add build date
    if lastBuildDate == None:
	lastBuildDate = ET.SubElement(channel, "lastBuildDate")
    pubDate = channel.find("pubDate")
    if pubDate == None:
	pubDate = ET.SubElement(channel, "pubDate")
    lastBuildDate.text = utcnow
    pubDate.text = utcnow
    
    # find if we need to remove an old item
    itemlist = channel.findall("item")
    for feedItem in itemlist:
	feedGuid = feedItem.find("guid")
	if feedGuid != None:
	    if feedGuid.text == guid.text:
		channel.remove(feedItem)
		
    # and append the new item
    channel.append(item)

    # wrap it in an ElementTree instance and save as XML
    print "Writing feed %s ..." % os.path.basename(rssPath)
    indent(rss) # not really required, but nice for debugging
    tree = ET.ElementTree(rss)
    tree.write(rssPath, encoding="utf-8", xml_declaration=True)
    print "Done!"

if __name__=="__main__":
    main(*sys.argv)
