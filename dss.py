# Module: dss
# - Retrives images from MAST DSS image server (fits or gif)
# - Computes positions from Digital Sky Survey plate fit
# Usage:
#       >>> import dss
#       >>> dss = dss.DSS()
#       >>> dss.getDSSImage('10:56:59.9', '-03:37:37.9', 'ms1054_dss.fits',
#       epoch='J2000', width=15.0, height=15.0)
#       >>> dss.getWCS('ms1054_dss.fits')
#       >>> ra, dec = dss.xy2rd(143, 343)
#       >>> print ra, dec
#       10:57:20.31  -3:39:23.40
#       >>> x, y = dss.rd2xy('10:57:20.31', ' -3:39:23.40')
#       >>> print x, y
#       142.985610883 343.0015852
# External modules needed:
#       fits - http://www.physics.uwa.edu.au/~andrew/
#
# DKM 2003-02-13

from math import pi,sin,cos,tan,atan,atan2
import os.path
import angles
import astropy.io.fits as fits

class DSS:
    def __init__(self):
        self.radeg = 180.0/pi
        self.twopi = 2.0*pi
        self.arcsec_per_radian = 3600.0*self.radeg

    def getWCS(self, fitsfile):
        self.fitsimg = fitsfile[0]
        #try:
        #    self.fitsimg = fits.FITS(self.fitsfile, "h")
        #except IOerror as err:
        #    print(err)
        #    return
        # Make a new wcs dictionary
        amdx = []
        amdy = []
        for i in range(1,14):
                amdx.append(float(self.fitsimg.header["AMDX"+str(i)]))
                amdy.append(float(self.fitsimg.header["AMDY"+str(i)]))
        rah = (float(self.fitsimg.header["PLTRAH"]) +
              float(self.fitsimg.header["PLTRAM"])/60.0 +
              float(self.fitsimg.header["PLTRAS"])/3600.0)
        plate_ra = angles.hrs2rad(rah)
        if "-" in self.fitsimg.header["PLTDECSN"]:
                decsn = -1
        else:
                decsn = 1
        decd = decsn*(float(self.fitsimg.header["PLTDECD"]) +
               float(self.fitsimg.header["PLTDECM"])/60.0 +
               float(self.fitsimg.header["PLTDECS"])/3600.0)
        plate_dec = angles.deg2rad(decd)

        self.wcs = {
              "xpoff" : float(self.fitsimg.header["CNPIX1"]),
              "ypoff" : float(self.fitsimg.header["CNPIX2"]),
              "xpsize" : float(self.fitsimg.header["XPIXELSZ"]),
              "ypsize" : float(self.fitsimg.header["YPIXELSZ"]),
              "ppo3" : float(self.fitsimg.header["PPO3"]),
              "ppo6" : float(self.fitsimg.header["PPO6"]),
              "xcoeff" : amdx,
              "ycoeff" : amdy,
              "plate_ra" : plate_ra,
              "plate_dec" : plate_dec,
              "platescl" : float(self.fitsimg.header["PLTSCALE"])
              }
        return

    def xy2rd(self, xin, yin):
        if not hasattr(self, 'wcs'):
            print("No wcs loaded!")
            return
        x = float(xin) - 0.5
        y = float(yin) - 0.5
        obx = (self.wcs["ppo3"]-(self.wcs["xpoff"]+x)*self.wcs["xpsize"])/1000.0
        oby = ((self.wcs["ypoff"]+y)*self.wcs["ypsize"]-self.wcs["ppo6"])/1000.0

        xi = (self.wcs["xcoeff"][0]*obx+               
              self.wcs["xcoeff"][1]*oby+               
              self.wcs["xcoeff"][2]+                   
              self.wcs["xcoeff"][3]*obx**2+             
              self.wcs["xcoeff"][4]*obx*oby+           
              self.wcs["xcoeff"][5]*oby**2+             
              self.wcs["xcoeff"][6]*(obx**2+oby**2)+     
              self.wcs["xcoeff"][7]*obx**3+             
              self.wcs["xcoeff"][8]*obx**2*oby+         
              self.wcs["xcoeff"][9]*obx*oby**2+         
              self.wcs["xcoeff"][10]*oby**3+               
              self.wcs["xcoeff"][11]*obx*(obx**2+oby**2)+   
              self.wcs["xcoeff"][12]*obx*(obx**2+oby**2)**2)

        eta = (self.wcs["ycoeff"][0]*oby+              
               self.wcs["ycoeff"][1]*obx+              
               self.wcs["ycoeff"][2]+                  
               self.wcs["ycoeff"][3]*oby**2+            
               self.wcs["ycoeff"][4]*oby*obx+          
               self.wcs["ycoeff"][5]*obx**2+            
               self.wcs["ycoeff"][6]*(obx**2+oby**2)+    
               self.wcs["ycoeff"][7]*oby**3+            
               self.wcs["ycoeff"][8]*oby**2*obx+        
               self.wcs["ycoeff"][9]*oby*obx**2+        
               self.wcs["ycoeff"][10]*obx**3+               
               self.wcs["ycoeff"][11]*oby*(obx**2+oby**2)+   
               self.wcs["ycoeff"][12]*oby*(obx**2+oby**2)**2)

        pltra = self.wcs["plate_ra"]
        pltdec = self.wcs["plate_dec"]

        xi = xi/self.arcsec_per_radian
        eta = eta/self.arcsec_per_radian

        numerator = xi/cos(pltdec)
        denominator = 1.0 - eta*tan(pltdec)
        ra = atan2(numerator,denominator) + pltra

        if ra < 0:
            ra = ra + self.twopi
        if ra > self.twopi:
            ra = ra - self.twopi

        numerator = cos(ra - pltra)
        denominator = (1.0 - eta*tan(pltdec))/(eta + tan(pltdec))
        dec = atan(numerator/denominator)

        ra = angles.dms2sex(angles.rad2hrs(ra))
        dec = angles.dms2sex(angles.rad2deg(dec))
        return ra, dec

    def rd2xy(self, ra, dec):
        if not hasattr(self, 'wcs'):
            print("No wcs loaded!")
            return
        ra = angles.hrs2rad(angles.sex2deg(ra))
        dec = angles.deg2rad(angles.sex2deg(dec))
        iters = 0
        maxiters=50
        tolerance=0.0000005
        pltra = self.wcs["plate_ra"]
        pltdec = self.wcs["plate_dec"]
        cosd = cos(dec)
        sind = sin(dec)
        ra_dif = ra - pltra
        div = (sind*sin(pltdec) + cosd*cos(pltdec)*cos(ra_dif))
        xi = cosd*sin(ra_dif)*self.arcsec_per_radian/div
        eta = (sind*cos(pltdec) - cosd*sin(pltdec)*cos(ra_dif))*self.arcsec_per_radian/div
        obx = xi/self.wcs["platescl"]
        oby = eta/self.wcs["platescl"]
        deltx = 10.0
        delty = 10.0
        while min([abs(deltx), abs(delty)]) > tolerance or iters < maxiters:
            f = (self.wcs["xcoeff"][0]*obx+                 
                 self.wcs["xcoeff"][1]*oby+                 
                 self.wcs["xcoeff"][2]+                     
                 self.wcs["xcoeff"][3]*obx*obx+             
                 self.wcs["xcoeff"][4]*obx*oby+             
                 self.wcs["xcoeff"][5]*oby*oby+             
                 self.wcs["xcoeff"][6]*(obx*obx+oby*oby)+   
                 self.wcs["xcoeff"][7]*obx*obx*obx+         
                 self.wcs["xcoeff"][8]*obx*obx*oby+         
                 self.wcs["xcoeff"][9]*obx*oby*oby+         
                 self.wcs["xcoeff"][10]*oby*oby*oby+             
                 self.wcs["xcoeff"][11]*obx*(obx*obx+oby*oby)+   
                 self.wcs["xcoeff"][12]*obx*(obx*obx+oby*oby)**2)

            fx = (self.wcs["xcoeff"][0]+                     
                  self.wcs["xcoeff"][3]*2.0*obx+             
                  self.wcs["xcoeff"][4]*oby+                 
                  self.wcs["xcoeff"][6]*2.0*obx+             
                  self.wcs["xcoeff"][7]*3.0*obx*obx+         
                  self.wcs["xcoeff"][8]*2.0*obx*oby+         
                  self.wcs["xcoeff"][9]*oby*oby+             
                  self.wcs["xcoeff"][11]*(3.0*obx*obx+oby*oby)+   
                  self.wcs["xcoeff"][12]*(5.0*obx**4 + 6.0*obx**2*oby**2 + oby**4))

            fy = (self.wcs["xcoeff"][1]+                     
                  self.wcs["xcoeff"][4]*obx+                 
                  self.wcs["xcoeff"][5]*2.0*oby+             
                  self.wcs["xcoeff"][6]*2.0*oby+             
                  self.wcs["xcoeff"][8]*obx*obx+             
                  self.wcs["xcoeff"][9]*obx*2.0*oby+         
                  self.wcs["xcoeff"][10]*3.0*oby*oby+        
                  self.wcs["xcoeff"][11]*2.0*obx*oby+        
                  self.wcs["xcoeff"][12]*(4.0*obx**3*oby + 4.0*obx*oby**3))

            g = (self.wcs["ycoeff"][0]*oby+                 
                 self.wcs["ycoeff"][1]*obx+                 
                 self.wcs["ycoeff"][2]+                     
                 self.wcs["ycoeff"][3]*oby*oby+             
                 self.wcs["ycoeff"][4]*oby*obx+             
                 self.wcs["ycoeff"][5]*obx*obx+             
                 self.wcs["ycoeff"][6]*(obx*obx+oby*oby)+   
                 self.wcs["ycoeff"][7]*oby*oby*oby+         
                 self.wcs["ycoeff"][8]*oby*oby*obx+         
                 self.wcs["ycoeff"][9]*oby*obx*obx+         
                 self.wcs["ycoeff"][10]*obx*obx*obx+             
                 self.wcs["ycoeff"][11]*oby*(obx*obx+oby*oby)+   
                 self.wcs["ycoeff"][12]*oby*(obx*obx+oby*oby)**2)

            gx = (self.wcs["ycoeff"][1]+                     
                  self.wcs["ycoeff"][4]*oby+                 
                  self.wcs["ycoeff"][5]*2.0*obx+             
                  self.wcs["ycoeff"][6]*2.0*obx+             
                  self.wcs["ycoeff"][8]*oby*oby+             
                  self.wcs["ycoeff"][9]*oby*2.0*obx+         
                  self.wcs["ycoeff"][10]*3.0*obx*obx+        
                  self.wcs["ycoeff"][11]*2.0*obx*oby+        
                  self.wcs["ycoeff"][12]*(4.0*obx**3*oby + 4.0*obx*oby**3))

            gy = (self.wcs["ycoeff"][0]+                     
                  self.wcs["ycoeff"][3]*2.0*oby+             
                  self.wcs["ycoeff"][4]*obx+                 
                  self.wcs["ycoeff"][6]*2.0*oby+             
                  self.wcs["ycoeff"][7]*3.0*oby*oby+         
                  self.wcs["ycoeff"][8]*2.0*oby*obx+         
                  self.wcs["ycoeff"][9]*obx*obx+             
                  self.wcs["ycoeff"][11]*(3.0*oby*oby+obx*obx)+   
                  self.wcs["ycoeff"][12]*(5.0*oby**4 + 6.0*obx**2*oby**2 + obx**4))

            f = f-xi
            g = g-eta
            deltx = (-f*gy+g*fy) / (fx*gy-fy*gx)
            delty = (-g*fx+f*gx) / (fx*gy-fy*gx)
            obx = obx + deltx
            oby = oby + delty
            iters = iters + 1

        x = (self.wcs["ppo3"] - obx*1000.0)/self.wcs["xpsize"] - self.wcs["xpoff"]
        y = (self.wcs["ppo6"] + oby*1000.0)/self.wcs["ypsize"] - self.wcs["ypoff"]
        x = x + 0.5
        y = y + 0.5
        return x, y 

    def skyPA(self):
        xc = float(self.fitsimg.header["NAXIS1"])/2.0
        yc = float(self.fitsimg.header["NAXIS2"])/2.0
        r1, d1 = self.xy2rd(xc, yc)
        r1 = angles.hrs2rad(angles.sex2deg(r1))
        d1 = angles.deg2rad(angles.sex2deg(d1))
        r2 = r1
        # Go 20" north
        d2 = d1 + 20.0/self.arcsec_per_radian
        r2 = angles.dms2sex(angles.rad2hrs(r2))
        d2 = angles.dms2sex(angles.rad2deg(d2))
        xn, yn = self.rd2xy(r2, d2)
        pan = angles.rad2deg(atan2((yn-yc), (xn-xc)))
        if pan < -90.0:
            pan = pan + 360.0
        if pan < -90.0:
            pa = 270.0 + pan
        else:
            pa = pan - 90.0
        return pa

    # def getDSSImage_astroquery(selfs, ra, dec, output, epoch='J2000', width=15.0, height=15.0):
    #     print("%s %s" % (ra, dec))
    #     print(epoch)
    #     print("retrieving DSS image")
    #     height = height * u.arcmin
    #     width = width * u.arcmin
    #     paths = SkyView.get_images(position="%s %s" % (ra,dec), survey='DSS', coordinates=epoch,
    #                              height=height, width=width)
    #     img = paths[0]
    #     img.writeto(output)


    def getDSSImage(self, ra, dec, output, epoch='J2000', width=15.0, height=15.0):
        ra.replace(':', '%3A')
        dec.replace(':', '%3A')
        if output.split('.')[-1] == 'fits':
            ftype = 'fits'
        if output.split('.')[-1] == 'gif':
            ftype = 'gif'
        pars = (ra, dec, epoch, str(width), str(height), ftype)
        url = 'https://archive.stsci.edu/cgi-bin/dss_search?v=2r&r=%s&d=%s&e=%s&h=%s&w=%s&f=%s&c=none&fov=NONE&v3=' % pars
        #mast = 'archive.stsci.edu'
        #h = http.client.HTTP(mast)
        #h.putrequest('GET', url)
        #h.putheader('Accept', 'text/html')
        #h.putheader('Accept', 'text/plain')
        #h.endheaders()
        #reply, msg, hdrs = h.getreply()
        #doc = h.getfile().read()
        #doc = requests.get(url).content
        #$print(doc.content)
        #if doc[:6] != 'SIMPLE':
        #    strip_html = re.compile(r'<[^>]*>')
        #    text = strip_html.sub('', doc)
        #    print('IOError:')
        #    raise IOError(text)
        #else:
        if os.path.exists(output):
            print("File %s already exists" % output)
            dat = fits.open(output)
        else:
            dat = fits.open(url)
            dat.writeto(output)
        return dat
        #f = open(output, 'w')
        #f.write(doc)
        #f.close()
