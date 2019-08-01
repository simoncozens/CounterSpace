from AppKit import NSView, NSColor, NSRectFill, NSBezierPath, NSAffineTransform
from vanilla import *
import traceback
import sys

class GlyphDrawView(NSView):
  def setMaster(self, master):
    self.master = master
    self.setNeedsDisplay_(True)

  def setString(self, string):
    self.string = string
    self.setNeedsDisplay_(True)

  def setDistances(self, distances):
    self.distances = distances
    self.setNeedsDisplay_(True)

  def drawRect_(self, rect):
    try:
      NSColor.whiteColor().set()
      NSRectFill(self.bounds())
      NSColor.blackColor().setFill()
      NSColor.blueColor().setStroke()
      p = NSBezierPath.bezierPath()
      xcursor = 0
      string = self.string
      master = self.master
      for s in range(0,len(string)):
        thisPath = NSBezierPath.bezierPath()
        gsglyph = master.font.glyphs[string[s]]
        layer   = gsglyph.layers[master.id]
        thisPath.appendBezierPath_(layer.completeBezierPath)
        # print("X cursor was",xcursor)
        xcursor = xcursor - layer.bounds.origin.x
        # print("Moving backwards", layer.bounds.origin.x)
        t = NSAffineTransform.transform()
        t.translateXBy_yBy_(xcursor,-master.descender)
        thisPath.transformUsingAffineTransform_(t)
        # print("Drawing at",xcursor)
        # print(thisPath)
        xcursor = xcursor + layer.bounds.origin.x
        xcursor = xcursor + layer.bounds.size.width
        # print("Adding width", layer.bounds.size.width)
        if s < len(string)-1:
          xcursor  = xcursor + self.distances[(string[s],string[s+1])]
        p.appendBezierPath_(thisPath)

      t = NSAffineTransform.transform()
      vscale = self.bounds().size.height / (master.ascender - master.descender)
      hscale = self.bounds().size.width / xcursor
      t.scaleBy_(min(hscale,vscale))
      p.transformUsingAffineTransform_(t)
      p.fill()
    except:
      print("Oops!",sys.exc_info()[0],"occured.")
      traceback.print_exc(file=sys.stdout)
