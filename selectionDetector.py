# -*- coding: utf-8 -*-
'''
    Selection detection algorithms (for gaze and hand-tracking applications
    
    Dominic Canare <dom@greenlightgo.org>
'''

import math
def distance(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    
def pointMean(pointList):
    return Point(
        sum(p.x for p in pointList) / len(pointList),
        sum(p.y for p in pointList) / len(pointList),
        sum(p.z for p in pointList) / len(pointList)
    )
    
class Point(object):
    def __init__(self, x=0, y=0, z=0, t=0, raw=None):
        self.x = x
        self.y = y
        self.z = z
        self.time = t
        self.raw = raw
        
    def __repr__(self):
        return "%d, %d, %d, %d : %s" % (self.x, self.y, self.z, self.time, self.raw)

'''
    Abstract class for selection detection
'''
class SelectionDetector(object):
    def __init__(self, bufferSize=256):
        self.points = []
        self.selection = None
        self.bufferSize = bufferSize
    
    '''
        @param point (x, y, z, time) tuple
    '''
    def addPoint(self, point):
        self.points.insert(0, point)
        
        if self.bufferSize != None:
            del self.points[self.bufferSize:]
    
    def clearSelection(self):
        selection = self.selection
        self.selection = None
        
        return selection


'''
    Selects points based on a user dwelling on a particular spot for a minimum amount of time.    
'''
class DwellSelect(SelectionDetector):
    def __init__(self, minimumDelayInSeconds, rangeInPixels):
        super(DwellSelect, self).__init__()
        self.minimumDelay = minimumDelayInSeconds
        self.range = rangeInPixels
        
        self.lastDwellPoint = None
        self.inDwell = False
        
    def setDuration(self, duration):
        self.minimumDelay = duration
        
    def setRange(self, rangeInPixels):
        self.range = rangeInPixels
        
    def addPoint(self, point):
        super(DwellSelect, self).addPoint(point)
        if len(self.points) < 2:
            return
        
        if self.inDwell and distance(self.lastDwellPoint, point) > self.range:
            self.inDwell = False
        
        if not self.inDwell:
            meanPoint = self.calculateDwellMean()
            if meanPoint != None:
                self.lastDwellPoint = meanPoint
                self.inDwell = True
                self.selection = meanPoint

    def calculateDwellMean(self):
        for i in range(1, len(self.points)):
            point = self.points[i]
            
            if distance(self.points[0], point) > self.range:
                break
                
            if self.points[0].time - point.time > self.minimumDelay:
                meanPoint = pointMean(self.points[:i])
                meanPoint.time = point.time
                
                return meanPoint
                
        return None
