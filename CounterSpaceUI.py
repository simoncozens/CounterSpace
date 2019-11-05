#MenuTitle: CounterSpace
# -*- coding: utf-8 -*-
__doc__="""
Autospace and autokern with counters
"""
from GlyphDrawView import GlyphDrawView
from GlyphsApp import Message
from AppKit import NSRunLoop
from vanilla import *
from itertools import tee,izip
import CounterSpace
import string
import traceback

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
    self.prespaced = { "caps": [], "caplower": [], "lower": [] }
    self.bare_minimum = 20
    self.serif_smoothing = 0
    self.view.setMaster(self.master)
    self.view.setFrame_(((0, 0), (880, 200)))
    self.view.setString("")
    self.w.scrollView = ScrollView((10, 380, -10, -10), self.view)

    self.w.textBox1 = TextBox((10,20,150,17),"Bare Minimum")
    self.w.bareMinSlider = Slider((180, 20, -60, 23), callback = self.bareMinCallback, minValue = 0, maxValue = 200)
    self.w.bareMinSlider.set(self.bare_minimum)
    self.w.bareMinTextBox = TextBox((-50,20,50,17),str(self.bare_minimum))
    self.w.textBox1b = TextBox((10,40,-10,14),"(Set this first. A good test string for this variable is 'HHLArvt')",sizeStyle="small",selectable=False)#,callback=self.setHHLHvt)

    self.w.textBox2 = TextBox((10,70,150,17),"Serif smoothing")
    self.w.serifSmoothSlider = Slider((180, 70, -60, 23), callback = self.serifSmoothCallback, minValue = 0, maxValue = 20, continuous=False)
    self.w.serifSmoothSlider.set(self.serif_smoothing)
    self.w.serifSmoothSlider.enable(False)
    self.w.serifSmoothTextBox = TextBox((-50,70,50,17),self.serif_smoothing)


    self.w.textBox3 = TextBox((10,100,150,17),"Spaced pairs list")
    self.w.spacedPairsList = EditText((180, 100, -60, 20), callback = self.setSpacedPairs,text="EE,AV",continuous=False)
    self.oldssp = ""
    self.w.textBox3b = TextBox((10,130,-10,14),"Comma-separated list of pairs whose spacing is used as an example. The following pairs are silently added: HH,OO,HO,OH, Ho,To,Th,Hh, oo,nn,on,no,te,rg,ge.",sizeStyle="small",selectable=False)

    self.w.recomputeButton = Button((10,170,150,17),"Compute parameters", callback = self.runSolver)
    self.w.textBoxRCP = TextBox((10,190,-10,14),"(NB: This takes a long time but you need to do it!)",sizeStyle="small",selectable=False)
    self.w.bar = ProgressBar((10, 220, -10, 16),minValue =0 , maxValue = 100)
    self.w.errorBox = TextBox((10, 250, -10, 16),"")

    self.w.editText = EditText((10, 360, 200, 20), callback=self.editTextCallback,text="HHOOLVAH")
    self.setSpacedPairs(self.w.spacedPairsList)
    self.w.editText.enable(False)
    self.w.open()

  def progress(self,err):
    self.w.errorBox.set("Error: %.7f" % err)
    self.w.errorBox._nsObject.setNeedsDisplay_(True)
    pairs = len(self.prespaced["caps"]) + len(self.prespaced["caplower"]) + len(self.prespaced["lower"])
    self.w.bar.increment(1.0/(3*pairs))
    NSRunLoop.mainRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.0001))

  def spacingClass(self,s):
    l,r = s[0],s[1]
    if l in string.ascii_uppercase and r in string.ascii_uppercase:
        return "caps"
    if l in string.ascii_uppercase and r in string.ascii_lowercase:
        return "caplower"
    return "lower"

  def setSpacedPairs(self,sender):
    if sender.get() == self.oldssp:
        return
    try:
        self.oldssp = sender.get()
        csl = sender.get().split(",")
        self.prespaced["caps"] = ["HH","OO","HO","OH"]
        self.prespaced["caplower"] = ["Ho","To","Th","Hh"]
        self.prespaced["lower"] = ["oo","nn","on","no","te","rg","ge"]
        for s in csl:
            self.prespaced[self.spacingClass(s)].append(s)
        for k in ["caps","caplower","lower"]:
            self.prespaced[k] = list(set(self.prespaced[k]))
        print("Set spaced pairs called")
        self.needsRecomputing()
    except Exception as e:
        print(e)
        traceback.print_exc()

  def needsRecomputing(self):
    self.spacers = {}
    for c in ["caps", "lower", "caplower"]:
        self.spacers[c] = CounterSpace.CounterSpace(self.master,
          bare_minimum=self.bare_minimum,
          serif_smoothing=self.serif_smoothing,
          key_pairs = self.prespaced[c]
        )
    self.w.recomputeButton.enable(True)
    self.w.editText.enable(False)
    self.spacing = {}

  def runSolver(self,sender):
    print("Prespaced dictionary:")
    print(self.prespaced)
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(processes=1)
    self.w.bar.set(0)
    self.w.recomputeButton.enable(False)

    for c in ["lower"]:
        print("Determining parameters for %s" % c)
        result = self.spacers[c].determine_parameters(callback = lambda err:self.progress(err))
        self.spacers[c].options = result
        print("Result for %s : %s" % (c,result))

    self.spacers["caps"].options = {'bottom_strength': 1.1345652573787253, 'h_top': 5.487824242337442, 'h_center': 5.931368743262439, 'h_bottom': 15.282101114272237, 'w_top': 27.21495352061693, 'w_center': 58.93266226658602, 'top_strength': 0.5915259512256053, 'center_strength': 0.07957667771756849, 'w_bottom': 12.07849643211549}
    # self.spacers["lower"].options =  {'bottom_strength': 5.236787909255455, 'h_top': -13.434270522062697, 'h_center': 47.60847066913675, 'h_bottom': 5.990015356494567, 'w_top': -7.108329693663322, 'w_center': 0.47190584344597786, 'top_strength': -0.9089546341683743, 'center_strength': 0.06563161642247345, 'w_bottom': 32.21412242837695}
    self.spacers["caplower"].options =  {'bottom_strength': -2.422052201203848, 'h_top': -12.393311309708867, 'h_center': 51.62401673223201, 'h_bottom': 12.732836126432804, 'w_top': 139.33317239248765, 'w_center': -0.7569307267200843, 'top_strength': 1.7618843046229808, 'center_strength': 7.0190999837101, 'w_bottom': 56.97695661416948}
    self.w.bar.set(100)
    self.spacing={}
    self.setStringAndDistances(self.w.editText.get())
    self.editTextCallback(self.w.editText)
    self.w.editText.enable(True)

    # pool.apply_async(f,callback = cb)

  def serifSmoothCallback(self, sender):
    serif_smoothing = int(sender.get())
    self.w.serifSmoothTextBox.set(str(serif_smoothing))
    self.serif_smoothing = serif_smoothing
    self.c.set_serif_smoothing(serif_smoothing)
    print("Serif callback called")
    self.needsRecomputing()

  def bareMinCallback(self, sender):
    bm = int(sender.get())
    self.w.bareMinTextBox.set(str(bm))
    for c in ["caps", "lower", "caplower"]:
        self.spacers[c].bare_minimum = bm
    self.spacing = {}
    self.editTextCallback(self.w.editText)

  def editTextCallback(self, sender):
    print("Edit text callback called")
    self.setStringAndDistances(sender.get())

  def get_spacing(self,l,r):
    if not (l,r) in self.spacing:
      c = self.spacingClass(l+r)
      self.spacing[(l,r)] = self.spacers[c].space(l,r)
      print("%s%s = %.5f" % (l,r,self.spacing[(l,r)]))
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
