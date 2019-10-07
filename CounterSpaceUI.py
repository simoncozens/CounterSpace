#MenuTitle: CounterSpace
# -*- coding: utf-8 -*-
__doc__="""
Autospace and autokern with counters
"""
from GlyphDrawView import GlyphDrawView
from GlyphsApp import Message
from vanilla import *
from itertools import tee,izip
import CounterSpaceGlyphs
import string

def pairwise(iterable):
  a, b = tee(iterable)
  next(b, None)
  return izip(a, b)

class CounterSpaceUI(object):
  def __init__(self):
    self.w = Window((900, 600))
    self.view = GlyphDrawView.alloc().init()
    self.master = Glyphs.font.selectedFontMaster
    self.spacing = {}
    self.bare_minimum = 20
    self.max_squish = 100
    self.top_strength = 1
    self.bottom_strength = 1
    self.serif_smoothing = 0
    self.descend_into_counters = self.master.xHeight
    self.centrality = 10
    self.view.setMaster(self.master)
    self.view.setFrame_(((0, 0), (880, 200)))
    self.view.setString("")
    self.w.scrollView = ScrollView((10, 380, -10, -10), self.view)

    self.w.textBox1 = TextBox((10,20,150,17),"Bare Minimum")
    self.w.bareMinSlider = Slider((180, 20, -60, 23), callback = self.bareMinCallback, minValue = 0, maxValue = 200, continuous=False)
    self.w.bareMinSlider.set(self.bare_minimum)
    self.w.bareMinTextBox = TextBox((-50,20,50,17),str(self.bare_minimum))
    self.w.textBox1b = TextBox((10,40,-10,14),"(Set this first. A good test string for this variable is 'HHLArvt')",sizeStyle="small",selectable=False)#,callback=self.setHHLHvt)

    self.w.textBox5 = TextBox((10,70,150,17),"Serif smoothing")
    self.w.serifSmoothSlider = Slider((180, 70, -60, 23), callback = self.serifSmoothCallback, minValue = 0, maxValue = 20, continuous=False)
    self.w.serifSmoothSlider.set(self.serif_smoothing)
    # XXX Disabled because for some reason the convolve hangs Glyphs. :-(
    self.w.serifSmoothSlider.enable(False)
    self.w.serifSmoothTextBox = TextBox((-50,70,50,17),self.serif_smoothing)

    self.w.recomputeButton = Button((10,100,150,17),"Compute parameters", callback = self.runSolver)
    self.w.textBoxRCP = TextBox((10,120,-10,14),"(NB: This takes a long time but you need to do it!)",sizeStyle="small",selectable=False)

    self.w.editText = EditText((10, 360, 200, 20), callback=self.editTextCallback,text="HHOOLVAH")
    self.c = CounterSpaceGlyphs.CounterSpace(self.master,
      bare_minimum=self.bare_minimum,
      serif_smoothing=self.serif_smoothing
    )
    self.w.editText.enable(False)
    self.w.open()

  def printDot(self,o):
    import sys
    sys.stdout.write(".")
    sys.stdout.flush()

  def runSolver(self,sender):
    self.c.determine_parameters(callback=self.printDot)

    print(self.c.options)
    self.spacing={}
    self.setStringAndDistances(self.w.editText.get())
    self.editTextCallback(self.w.editText)
    self.w.recomputeButton.enable(False)
    self.w.editText.enable(True)

  def serifSmoothCallback(self, sender):
    serif_smoothing = int(sender.get())
    self.w.serifSmoothTextBox.set(str(serif_smoothing))
    self.serif_smoothing = serif_smoothing
    self.c.set_serif_smoothing(serif_smoothing)
    self.w.recomputeButton.enable(True)
    self.w.editText.enable(False)

  def bareMinCallback(self, sender):
    bm = int(sender.get())
    self.w.bareMinTextBox.set(str(bm))
    self.bare_minimum = bm
    self.w.recomputeButton.enable(True)
    self.w.editText.enable(False)

  def editTextCallback(self, sender):
    print("Edit text callback called")
    self.setStringAndDistances(sender.get())

  def get_spacing(self,l,r):
    if not (l,r) in self.spacing:
      self.spacing[(l,r)] = self.c.space(l,r)
    return self.spacing[(l,r)]

  def setStringAndDistances(self, string):
    string_a = list(string)
    for i in range(0,len(string_a)):
      if ord(string_a[i]) > 255:
        string_a[i] = "%04x" % ord(string_a[i])
    print(string_a)
    for l,r in pairwise(string_a):
      self.get_spacing(l,r)
    self.view.setString(string_a)
    self.view.setDistances(self.spacing)

  def set_kerning(self,l,r):
    target = self.c.space(l,r)
    sofar =  (master.font.glyphs[l].layers[master.id].RSB + master.font.glyphs[r].layers[master.id].LSB)
    kern = target - sofar
    self.master.font.setKerningForPair(master.id, l,r,kern)
    return kern

  def set_sidebearings(self, g):
    lsb, rsb = self.c.derive_sidebearings(g)
    layer = self.master.font.glyphs[g].layers[self.master.id]
    layer.LSB = lsb
    layer.RSB = rsb

# Check we have the bare minimum glyphs defined
notThere = ""
master = Glyphs.font.selectedFontMaster
for g in "HOLVA":
    glyph = master.font.glyphs[g].layers[master.id]
    if len(glyph.paths) < 1:
        notThere = notThere + g
if len(notThere) > 0:
    Message("Required glyphs not defined: %s" % (",".join(notThere)), "CounterSpace")
else:
    CounterSpaceUI()
