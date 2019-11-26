#!/usr/bin/env python

"""Given a set of DEIMOS DSIMULATOR ASCII output files, Generates HTML
pages showing predicted DEIMOS guider image views based on DSS images.

Usage:
        Change to directory with your mask designs
        deimos_guider_dss [-D] [file1 .. fileN]

Switches:
        -D = debug mode; print each input line as it is processed

Args:
        fileN = DSIMULATOR output file list
       
External modules needed:
        PIL - http://www.pythonware.com/products/pil/

Examples:
        1) Generate finder charts for DSIMULATOR files mask1.out and
        mask2.out:
                deimos_guider_dss mask1.out mask2.out

        2) Generate finder charts for DSIMULATOR files mask1.out and
        mask2.out with debugging output:
                deimos_guider_dss -D mask1.out mask2.out

Modification History:
        2003-Mar-28     DKM     Original version
        2012-Nov-11     GDW     Fixed print format to handle -10<Dec<0
        2013-Mar-10     GDW     - Reverted mods from Nov, which broke
                                behavior at -1 < Dec < 0;
                                - Removed code which turned all spaces in
                                target name to underscores in starlist;
                                - Round all guider coords to nearest int
                                - Move guide star labels closer to star
        2013-Aug-27     GDW     - Add sanity check for undefined values on
                                tv coords
                                - add offsets in tv x and y
        2013-Sep-08     GDW     - Fixed problem with double-minus in DEC
                                - Added offsets to printout
        2013-Dec-20     GDW     - Added debug mode switch
                                """

import PIL.Image as Image, PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import fits2pil
from pathlib import Path

class selectedObject:
    def __init__(self, objectlist):
        self.id = objectlist[0]
        self.ra = objectlist[1]
        self.dec = objectlist[2]
        self.equinox = objectlist[3]
        self.magnitude = objectlist[4]
        self.passband = objectlist[5]
        self.priority_code = objectlist[6]
        self.sample = objectlist[7]
        self.select_flag = objectlist[8]
        self.pa_slit = objectlist[9]
        self.l1 = objectlist[10]
        self.l2 = objectlist[11]
        self.slitwidth = objectlist[12]

class guideStarObject(selectedObject):
    def __init__(self, objectlist):
        selectedObject.__init__(self, objectlist)
        self.xTV = None
        self.yTV = None

class Mask:
    def __init__(self):
        self.selectedObjects = []
        self.alignmentStars = []
        self.guideStars = []
        self.debug = False

    def readMaskFile(self, maskfile):

        print("Processing file %s" % maskfile)

        self.file = maskfile
        f = open(self.file,"r")
        l = f.readlines()
        f.close()

        # parse the second line of the file, which contains the field
        # name, field center, and equinox...
        if self.debug:
            print(l[1])
        pattern = "^(.+)\s+(\d+:\d+:\d+\.\d+)\s+(\S*\d+:\d+:\d+\.\d+)\s+(\S+)\s+PA=\s*(\S*)\s+##"
        mobj = re.match( pattern, l[1])
        if mobj:
            self.name = mobj.group(1)
            self.ra = mobj.group(2)
            self.dec = mobj.group(3)
            self.equinox = float(mobj.group(4))
            self.pa = float(mobj.group(5))
        else:
            print('  ERROR: line 2 does not match expected format -- abort!')
            sys.exit(1)

        if self.debug:
            print(l[3])
        c = l[3].split()
        self.guider_ra = c[3]
        self.guider_dec = c[4]
        a = l.index("# Selected Objects:\n")+2
        b = l.index("# Selected Guide Stars:\n")-1
        for r in l[a:b]:
            if self.debug:
                print(r)
            c = r.split()
            n = len(c)
            if n < 13:
                for i in range(13-n):
                    c.append(None)
            fc = [3, 4, 10, 11, 12]
            ic = [6, 7, 8]
            for i in range(n):
                if i is not None:
                    if i in fc:
                        c[i] = float(c[i])
                    if i in ic:
                        c[i] = int(c[i])
                    if i == 9:
                        if c[i] == 'INDEF':
                            c[i] = None
                        else:
                            c[i] = float(c[i])
            so = selectedObject(c)
            if so.priority_code == -1:
                self.guideStars.append(guideStarObject(c))
            elif so.priority_code == -2:
                self.alignmentStars.append(selectedObject(c))
            else:
                self.selectedObjects.append(selectedObject(c))
        a = l.index("# Selected Guide Stars:\n")+2
        try:
            b = l.index("# Non-Selected Objects:\n")-1
        except ValueError:
            b = len(l)
        for r in l[a:b]:
            if self.debug:
                print(r)
            c = r.split()
            if c[0] == "#":
                for gs in self.guideStars:
                    if gs.id == c[1]:
                        gs.xTV = float(c[6])
                        gs.yTV = float(c[7])

        # scan for bad entries...
        rejects=[]
        for gs in self.guideStars:
            if gs.xTV is None or gs.yTV is None:
                print("  WARNING: bad coords for guidestar %s (x=%s y=%s); rejected" % (gs.id, gs.xTV, gs.yTV))
                rejects.append(gs)
            else:
                gs.xTV += offset_x
                gs.yTV += offset_y
                print("  corrected coords for guidestar %s (x=%s y=%s)" % (gs.id, gs.xTV, gs.yTV))

        # remove bogus entries...
        for gs in rejects:
            self.guideStars.remove(gs)

def drawbox(pil_draw_obj, x, y, w, l):
    x1 = x - w/2
    y1 = y - w/2
    x2 = x + w/2
    y2 = y + w/2
    pil_draw_obj.rectangle((x1,y1,x2,y2))

def drawcircle(pil_draw_obj, x, y, r):
    pil_draw_obj.arc((x-r, y-r, x+r, y+r), 0, 360)

def drawcompass(pil_draw_obj, x, y, angle, fill=None):
    d2r = math.pi/180.0
    if angle < 0.0:
        angle = angle + 360.0
    pa = (180 + angle)*d2r
    r = 25
    # North vector
    dx = r*math.cos(pa)
    dy = r*math.sin(pa)
    x1 = x + dx
    y1 = y + dy
    tx1 = x + dx*1.5
    ty1 = y + dy*1.5
    pil_draw_obj.line((x, y, x1, y1), fill)
    pil_draw_obj.text((tx1, ty1), 'N', fill)
    # East vector
    dx = r*math.cos(pa+90*d2r)
    dy = r*math.sin(pa+90*d2r)
    x2 = x - dx
    y2 = y - dy
    tx2 = x - dx*1.5
    ty2 = y - dy*1.5
    pil_draw_obj.line((x, y, x2, y2), fill)
    pil_draw_obj.text((tx2, ty2), 'E', fill)

def rotxy(x, y, angle):
    # angle must be in radians
    rx = x*math.cos(angle) - y*math.sin(angle)
    ry = x*math.sin(angle) + y*math.cos(angle)
    return [rx, ry]

colors = {'red':        (255,   0,   0),
          'yellow':     (255, 255,   0),
          'green':      (  0, 255,   0),
          'cyan':       (  0, 255, 255),
          'blue':       (  0,   0, 255),
          'pink':       (255,   0, 255),
          'white':      (255, 255, 255),
          'black':      (  0,   0,   0),
          'light_grey': (224, 224, 224),
          'grey':       (200, 200, 200),
          'dark_grey':  ( 96,  96,  96), 
          'cbu_red':    (146,  21,  47),
          'navy_blue':  (  0,   0, 128)}

def to_jpg(data):# Clip data to brightness limits
    data[data > vmax] = vmax
    data[data < vmin] = vmin
    # Scale data to range [0, 1]
    data = (data - vmin)/(vmax - vmin)
    # Convert to 8-bit integer
    data = (255*data).astype(np.uint8)
    # Invert y axis
    data = data[::-1, :]

    # Create image from data array and save as jpg
    image = Image.fromarray(data, 'L')
    return(image)

if __name__ == '__main__':
    import os
    import sys
    import dss
    import math
    import re
    import getopt

    usage = "Usage: "+sys.argv[0]+" [-h] [-d] filename .. filenameN"

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hD')
    except getopt.GetoptError as err:
        print(err)
        print(usage)
        sys.exit(2)

    debug = True
    for o,a in optlist:
        if o == "-h":
            print(usage)
            sys.exit(1)
        elif o in "-D":
            print("DEBUG mode enabled")
            debug = True
        else:
            assert False, "unhandled option"
        
    mlist = args
    slf = open('starlist', 'w')
    base_path = Path(__file__).parent
    fontpath = (base_path / "Fonts")

    guider_scale = 0.207           # guider camera scale arcsec/pix
    guider_ccd = [212, 212]        # guider camera size in arcsec
    offset_x = 13                  # offset in X
    offset_y = -2                  # offset in Y
    print("Adopted TV offsets are dX=%+d and dY=%+d\n" % (offset_x,offset_y))
    
    # build html for master guider image list
    gdoc = []
    gdoc.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">\n')
    gdoc.append('<HTML>\n<HEAD>\n<TITLE>Guider Images</TITLE>\n</HEAD>\n')
    gdoc.append('<BODY BGCOLOR="#FFFFFF">\n<H1>Guider Images</H1>\n')
    gdoc.append('<OL type="square">\n<OL type="square">')
    dss = dss.DSS()
    for ml in mlist:
        input = ml
        # make mask instanace
        m = Mask()
        m.debug = debug
        try:
            m.readMaskFile(input)
        except Exception as err:
            print('ERROR: Unable to read mask file: '+ml)
            print(err)
            sys.exit(1)

        # set output file names
        output = m.name.strip()

        # remove spaces from name...
        output = re.sub( '\s', '_', output)
        fitsout = output+'_dss.fits'
        gifout = output+'_dss.gif'
        guider_gifout = output+'_guider_dss.gif'
        htmlout = output+'_dss.html'
        
        # add mask name to guider master list
        gdoc.append('<LI><A HREF="%s">%s</A>' % (htmlout, m.name))
        
        # build starlist
        # Modified by DKM 2009-03-30: Added PA info
        sra = m.ra.split(':')
        sdec = m.dec.split(':')
        srah = int(sra[0])
        sram = sra[1]
        sras = sra[2]
        sdech = sdec[0]
        sdecm = sdec[1]
        sdecs = sdec[2]
        spa = float(m.pa)

        # determine whether the DEC is + or -.  NOTE: this is
        # necessary because simply printing the DEC in %+03i format
        # will yield "+00" for -1 < Dec < 0!
        mobj = re.match( "^-", sdech)
        if mobj:
            sign = '-'
        else:
            sign = '+'
        adech = abs(int(sdech))

        # Sky's got no love for a negative PA
        if spa < 0:
            spa += 360
        seqnx = str(m.equinox).split('.')[0]
        targname = m.name[:16]
        slist = (targname,srah,sram,sras,sign,adech,sdecm,sdecs,seqnx,spa)
        sformat = '%-16s  %02i %s %s %s%02i %s %s %s rotdest=%.2f rotmode=pa\n'
        print("  "+sformat % slist)
        slf.write(sformat % slist)

        # generate a new Dec string which has +/-
        dec2 = '%s%02i:%s:%s' % (sign,adech,sdecm,sdecs)
        
        # get DSS image, draw guider, mark stars
        # Note: Assumed that DSS images are from 2nd generation red images
        # which are scanned at a resolution of 1"/pix.
        gra = m.guider_ra
        gdec = m.guider_dec
        try:
            fits_file = dss.getDSSImage(gra, gdec, fitsout)
        except IOError as error:
            print(error)
            sys.exit()
        dss.getWCS(fits_file)
        imfits2pil = fits2pil.arrayToGreyImage(fits_file[0].data)
        im = imfits2pil.convert('RGB')
        imskypa = dss.skyPA()
        rotate = 91.4 - m.pa
        gxy = (im.size[0]/2, im.size[1]/2)
        im = im.rotate(rotate, Image.BICUBIC)
        draw = ImageDraw.Draw(im)
        font=ImageFont.load(fontpath / "helvR08.pil")
        #draw.setfont(font)
        #draw.setink(colors['black'])
        draw.line((gxy[0]-106, gxy[1]+23, gxy[0]+106, gxy[1]+23), fill=colors['black'])
        drawbox(draw, gxy[0], gxy[1], 212, 212)
        for gs in m.guideStars:
            gsx, gsy = dss.rd2xy(gs.ra, gs.dec)
            radrot = rotate*(math.pi/180.0)
            gsrxy = rotxy(gsx - gxy[0], gsy - gxy[1], radrot)
            gsrxy[0] = gsrxy[0] + gxy[0]
            gsrxy[1] = im.size[1] - (gxy[1] + gsrxy[1])
            #draw.setink(colors['red'])
            label = gs.id.upper()
            draw.text((gsrxy[0]+10, gsrxy[1]-10), label, font = font, fill=colors['red'])
            drawcircle(draw, gsrxy[0], gsrxy[1], 10)
        #draw.setink(colors['blue'])
        drawcompass(draw, gxy[0]-116, gxy[1]-116, m.pa-imskypa, fill=colors['blue'])
        #font=ImageFont.load(fontpath+"/helvR12.pil")
        #draw.setfont(font)
        im = im.crop((gxy[0]-160, gxy[1]-160, gxy[0]+160, gxy[1]+160))
        im.save(guider_gifout)
        
        # build html for guider image
        doc = []
        doc.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">\n')
        doc.append('<HTML>\n<HEAD>\n<TITLE>%s</TITLE>\n</HEAD>\n' % m.name)
        doc.append('<BODY BGCOLOR="#FFFFFF">\n')
        doc.append('<H1 align="center">%s</H1>\n' % m.name)
        doc.append('<H3 align="center">Mask Coordinates</H3>\n')
        doc.append('<center><TABLE border=1 cellpadding=4 cellspacing=1 width="95%">\n')
        doc.append('<center><TABLE border=1 cellpadding=4 cellspacing=1 \
        width="95%"><TR Align=center> <TH ColSpan=1 \
        bgcolor="#B0C4DE">RA</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">DEC</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">Equinox</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">PA</TH></TR>\n')
        doc.append('<TR><TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % m.ra)
        doc.append('<TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % dec2)
        doc.append('<TD Align="center"  bgcolor="#E0F4FF">%4.1f</TD>\n' % m.equinox)
        doc.append('<TD Align="center"  bgcolor="#E0F4FF">%3.1f</TD>\n' % m.pa)
        doc.append('</TR>\n</TABLE><P>\n</center>\n')
        doc.append('<H3 align="center">Guider Image</H3>\n')
        doc.append('<center><IMG src="%s" height="320" \
        width="320" alt="%s"></center>\n' % (guider_gifout, guider_gifout))
        doc.append('<H3 align="center">Guider Stars</H3>\n')
        doc.append('<center>\n')
        doc.append('Applied offsets: ')
        doc.append('&Delta;X=%+d, ' % offset_x)
        doc.append('&Delta;Y=%+d'   % offset_y)
        doc.append('</center><p>\n')

        doc.append('<center><TABLE border=1 cellpadding=4 cellspacing=1 \
        width="95%"> <TR Align="center"> <TH ColSpan=1 \
        bgcolor="#B0C4DE">ID</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">RA</TH><TH ColSpan=1 bgcolor="#B0C4DE">DEC</TH><TH \
        ColSpan=1 bgcolor="#B0C4DE">Equinox</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">Mag</TH><TH ColSpan=1 bgcolor="#B0C4DE">Band</TH><TH ColSpan=1 \
        bgcolor="#B0C4DE">xTV</TH><TH ColSpan=1 bgcolor="#B0C4DE">yTV</TH></TR>\n')
        # mark guider stars
        for gs in m.guideStars:
            doc.append('<TR><TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % gs.id)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % gs.ra)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % gs.dec)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%4.1f</TD>\n' % gs.equinox)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%2.1f</TD>\n' % gs.magnitude)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%s</TD>\n' % gs.passband)
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%d</TD>\n' % round(gs.xTV))
            doc.append('<TD Align="center"  bgcolor="#E0F4FF">%d</TD></TR>\n' % round(gs.yTV))

        doc.append('</TABLE></center><P>')

        doc.append('</BODY></HTML>')
        maskdoc = open(htmlout, 'w')
        for l in doc:
            maskdoc.write(l)
        maskdoc.close()
    gdoc.append('<LI><A HREF="starlist">starlist</A>\n')
    gdoc.append('</OL>\n</OL>\n</BODY> </HTML>')
    guiderdoc = open('guider_images.html', 'w')
    for l in gdoc:
        guiderdoc.write(l)
    guiderdoc.close()
    cdir = os.getcwd()
    print('Point your browser to -> file://'+cdir+'/guider_images.html')
