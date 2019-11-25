#!/usr/bin/env python

import Numeric
import fits
import Image
import ImageChops
import sys

def zScale(a):
    mean = Numeric.add.reduce(Numeric.ravel(a))/(Numeric.multiply.reduce(a.shape)*1.)
    var = (Numeric.add.reduce(Numeric.power(Numeric.ravel(a)-mean,2)))/(Numeric.multiply.reduce(a.shape)-1.)
    std = Numeric.sqrt(var)
    return mean - 3*std, mean + 7*std
    
def arrayToGreyImage(a):
    z1, z2 = zScale(a)
    bzero = z1
    bscale = (z2 - z1)/256.0
    a = Numeric.divide(Numeric.subtract(a, bzero), bscale)
    a = Numeric.clip(a, 0, 255.0)
    a = a.astype('b')    # needed so a.tostring() method returns single bytes
    a = a[::-1]
    i = Image.fromstring('L', (a.shape[1], a.shape[0]), a.tostring())
    return ImageChops.invert(i)


if __name__ == '__main__':
    infile = sys.argv[1]
    output = sys.argv[2]
    f = fits.FITS(infile, 'r')
    im = arrayToGreyImage(f.data)
    im.save(output)
