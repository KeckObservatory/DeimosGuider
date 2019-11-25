import math

def hrs2rad(hr):
    """Converts hours to radians"""
    return hr*(math.pi/12.0)

def rad2hrs(rad):
    """Converts radians to hours"""
    return rad*(12.0/math.pi)

def deg2rad(deg):
    """Converts degrees to radians"""
    return deg*(math.pi/180.0)

def rad2deg(rad):
    """Converts radians to degrees"""
    return rad*(180.0/math.pi)

def hrs2deg(hr):
    """Converts hours to degrees"""
    return hr*(180.0/12.0)

def deg2hrs(deg):
    """Converts degrees to hours"""
    return deg*(12.0/180.0)

def dms2sex(deg):
    """Converts a number to sexagesimal (dddd:mm:ss.ss)"""
    precision = 2
    minfw = precision + 3
    ddeg = float('%.*f' % (2, deg*3600.0))/3600.0
    if ddeg == -0.0:
        ddeg == 0.0
    (ndeg, frac) = divmod(abs(ddeg), 1.0)
    if ddeg < 0:
        ndeg = -ndeg
    (nmin, frac) = divmod(frac*60.0, 1.0)
    nsec = frac*60.0
    return "%.0f:%02.0f:%0*.*f" % (ndeg, nmin, minfw, precision, nsec)


def sex2deg(sex):
    """Converts sexagesimal to degrees"""
    dms = sex.strip().split(':')
    if dms[0][0] == '-':
        sign = -1.0
        dms[0] = dms[0].replace('-','')
    else:
        sign = 1.0
    dms = [float(s) for s in dms]
    return sign*(dms[0] + dms[1]/60.0 + dms[2]/3600.0)
