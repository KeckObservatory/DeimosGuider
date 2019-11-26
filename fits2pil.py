#!/usr/bin/env python

import numpy as np
from astropy.io import fits
from PIL import Image
from PIL import ImageChops
import sys

def zScale(a):
    mean = np.add.reduce(np.ravel(a))/(np.multiply.reduce(a.shape)*1.)
    var = (np.add.reduce(np.power(np.ravel(a)-mean,2)))/(np.multiply.reduce(a.shape)-1.)
    std = np.sqrt(var)
    return mean - 3*std, mean + 7*std
    
def arrayToGreyImage(a):
    z1, z2 = zScale(a)
    bzero = z1
    bscale = (z2 - z1)/256.0
    a = np.divide(np.subtract(a, bzero), bscale)
    a = np.clip(a, 0, 255.0)
    a = a.astype('b')    # needed so a.tostring() method returns single bytes
    a = a[::-1]
    i = Image.frombytes('L', (a.shape[1], a.shape[0]), a.tostring())
    return ImageChops.invert(i)


if __name__ == '__main__':
    infile = sys.argv[1]
    output = sys.argv[2]
    f = fits.open(infile, 'r')
    im = arrayToGreyImage(f.data)
    im.save(output)
