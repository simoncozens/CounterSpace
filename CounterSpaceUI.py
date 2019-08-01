#MenuTitle: CounterSpace
# -*- coding: utf-8 -*-
__doc__="""
Autospace and autokern with counters
"""
from GlyphDrawView import GlyphDrawView
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
    self.master = Layer.master
    self.bare_minimum = 20
    self.max_squish = 100
    self.top_strength = 1
    self.bottom_strength = 1
    self.serif_smoothing = 0
    self.descend_into_counters = Layer.master.xHeight
    self.centrality = 10
    self.view.setMaster(Layer.master)
    self.view.setFrame_(((0, 0), (880, 200)))
    self.w.scrollView = ScrollView((10, 380, -10, -10), self.view)

    self.w.textBox1 = TextBox((10,50,150,17),"Bare Minimum")
    self.w.bareMinSlider = Slider((180, 50, -60, 23), callback = self.bareMinCallback, minValue = 0, maxValue = 200, continuous=False)
    self.w.bareMinSlider.set(self.bare_minimum)
    self.w.bareMinTextBox = TextBox((-50,50,50,17),str(self.bare_minimum))
    self.w.textBox1b = TextBox((10,70,-10,14),"(Set this first. A good test string for this variable is 'HHLArvt')",sizeStyle="small",selectable=False)#,callback=self.setHHLHvt)


    self.w.textBox2 = TextBox((10,100,150,17),"General tightness")
    self.w.textBox2b = TextBox((10,120,-10,14),"(A good test string for this variable is 'HHXOOXnin')",sizeStyle="small",selectable=False)#,callback=self.setHHOOH)

    self.w.centralitySlider = Slider((180, 100, -60, 23), callback = self.centralityCallback, minValue = 10, maxValue = Layer.master.xHeight, continuous=False)
    self.w.centralitySlider.set(self.centrality)
    self.w.centralityTextBox = TextBox((-50,100,50,17),str(self.centrality))

    self.w.textBox3 = TextBox((10,150,150,17),"Counter depth")
    self.w.textBox3b = TextBox((10,170,-10,14),"(A good test string for this variable is 'KOSOVO')",sizeStyle="small",selectable=False)#,callback=self.setHHOOAVAH)

    self.w.counterDepthSlider = Slider((180, 150, -60, 23), callback = self.counterDepthCallback, minValue = 1, maxValue = Layer.master.xHeight, continuous=False)
    self.w.counterDepthSlider.set(self.descend_into_counters)
    self.w.counterDepthTextBox = TextBox((-50,150,50,17),str(self.descend_into_counters))

    self.w.textBox4 = TextBox((10,200,150,17),"Top distance")
    self.w.textBoxgb = TextBox((10,220,-10,14),"(Controls close top pairs eg 'HTArn')",sizeStyle="small",selectable=False)#,callback=self.setHHVLAPH)

    self.w.topStrengthSlider = Slider((180, 200, -60, 23), callback = self.topStrengthCallback, minValue = 0, maxValue = 50, continuous=False)
    self.w.topStrengthSlider.set(self.top_strength)
    self.w.topStrengthTextBox = TextBox((-50,200,50,17),self.top_strength)

    self.w.textBox5 = TextBox((10,250,150,17),"Bottom distance")
    self.w.textBox5b = TextBox((10,270,-10,14),"(Controls close bottom pairs eg 'HLVtx')",sizeStyle="small",selectable=False)#,callback=self.setHHVLAPH)

    self.w.bottomStrengthSlider = Slider((180, 250, -60, 23), callback = self.bottomStrengthCallback, minValue = 0, maxValue = 50, continuous=False)
    self.w.bottomStrengthSlider.set(self.bottom_strength)
    self.w.bottomStrengthTextBox = TextBox((-50,250,50,17),self.bottom_strength)

    # self.w.textBox6 = TextBox((10,300,150,17),"Maximum squish")
    # self.w.textBox6b = TextBox((10,320,-10,14),"('LV')",sizeStyle="small",selectable=False)#,callback=self.setHHLHvt)
    # self.w.maxSquishSlider = Slider((180, 300, -60, 23), callback = self.maxSquishCallback, minValue = 0, maxValue = 200, continuous=False)
    # self.w.maxSquishSlider.set(self.max_squish)
    # self.w.maxSquishTextBox = TextBox((-50,300,50,17),str(self.max_squish))

    # self.w.textBox5 = TextBox((10,250,150,17),"Serif smoothing")

    # self.w.serifSmoothSlider = Slider((180, 250, -60, 23), callback = self.serifSmoothCallback, minValue = 0, maxValue = 20, continuous=False)
    # self.w.serifSmoothSlider.set(self.serif_smoothing)
    # # XXX Disabled because for some reason the convolve hangs Glyphs. :-(
    # self.w.serifSmoothSlider.enable(False)
    # self.w.serifSmoothTextBox = TextBox((-50,250,50,17),self.serif_smoothing)

    self.w.editText = EditText((10, 360, 200, 20), callback=self.editTextCallback,text="HHOOLVAH")
    self.c = CounterSpaceGlyphs.CounterSpace(self.master,
      magic_number = int(self.master.xHeight),
      factor=1.0/6.0,
      bare_minimum=self.bare_minimum,
      max_squish = self.max_squish,
      top_strength=self.top_strength,
      bottom_strength=self.bottom_strength,
      descend_into_counters=self.descend_into_counters,
      centrality=self.centrality,
      italic_angle = self.master.italicAngle,
      serif_smoothing=self.serif_smoothing
    )
    self.rebuildCounterspace()
    self.w.open()

  def setHHLHvt(self):
    self.w.editText.set("HHLVHvt")

  def setHHLHvt(self):
    self.w.editText.set("HHOOH")

  def setHHOOAVAH(self):
    self.w.editText.set("HHOOAVAH")

  def setHHVLAPH(self):
    self.w.editText.set("HHVLAPH")

  def rebuildCounterspace(self):
    self.c.bare_minimum = self.bare_minimum
    self.c.max_squish = self.max_squish
    self.c.top_strength = self.top_strength
    self.c.bottom_strength = self.bottom_strength
    self.c.descend_into_counters = self.descend_into_counters
    self.c.centrality = self.centrality
    self.c.serif_smoothing = self.serif_smoothing
    self.c._pair_areas = {}
    self.setStringAndDistances(self.w.editText.get())
    self.editTextCallback(self.w.editText)

  def centralityCallback(self, sender):
    centrality = int(sender.get())
    self.w.centralityTextBox.set(str(centrality))
    self.centrality = centrality
    self.rebuildCounterspace()

  def counterDepthCallback(self, sender):
    counter_depth = int(sender.get())
    self.w.counterDepthTextBox.set(str(counter_depth))
    self.descend_into_counters = counter_depth
    self.rebuildCounterspace()

  def topStrengthCallback(self, sender):
    top_strength = sender.get()
    self.w.topStrengthTextBox.set("%.1f" % top_strength)
    self.top_strength = top_strength
    self.rebuildCounterspace()

  def bottomStrengthCallback(self, sender):
    bottom_strength = sender.get()
    self.w.bottomStrengthTextBox.set("%.1f" % bottom_strength)
    self.bottom_strength = bottom_strength
    self.rebuildCounterspace()

  def serifSmoothCallback(self, sender):
    serif_smoothing = int(sender.get())
    self.w.serifSmoothTextBox.set(str(serif_smoothing))
    self.serif_smoothing = serif_smoothing
    self.c.set_serif_smoothing(serif_smoothing)
    self.rebuildCounterspace()

  def bareMinCallback(self, sender):
    bm = int(sender.get())
    self.w.bareMinTextBox.set(str(bm))
    self.bare_minimum = bm
    self.rebuildCounterspace()

  def maxSquishCallback(self, sender):
    bm = int(sender.get())
    self.w.maxSquishTextBox.set(str(bm))
    self.max_squish = bm
    self.rebuildCounterspace()

  def editTextCallback(self, sender):
    print("Edit text callback called")
    self.setStringAndDistances(sender.get())

  def setStringAndDistances(self, string):
    string_a = list(string)
    for i in range(0,len(string_a)):
      if ord(string_a[i]) > 255:
        string_a[i] = "%04x" % ord(string_a[i])
    print(string_a)
    distances = {}
    for l,r in pairwise(string_a):
      distances[(l,r)] = self.c.space(l,r)
    self.view.setString(string_a)
    self.view.setDistances(distances)

  def get_kerning(self,l,r):
    target = self.c.space(l,r)
    sofar =  (master.font.glyphs[l].layers[master.id].RSB + master.font.glyphs[r].layers[master.id].LSB)
    kern = target - sofar
    Layer.master.font.setKerningForPair(master.id, l,r,kern)
    return kern

  def set_sidebearings(self, g):
    lsb, rsb = self.c.derive_sidebearings(g)
    layer = Layer.master.font.glyphs[g].layers[Layer.master.id]
    layer.LSB = lsb
    layer.RSB = rsb

CounterSpaceUI()