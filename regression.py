from CounterSpace import CounterSpace

import unittest

test_fonts = ["CrimsonRoman.otf", "Tinos-Italic.ttf", "PTSerif-Italic.ttf", "Crimson-SemiboldItalic.otf", "OpenSans-Regular.ttf"]
spacers = {}

for f in test_fonts:
  serif_smoothing = 3
  if "OpenSans" in f:
    serif_smoothing = 0
  spacers[f] = CounterSpace(f,serif_smoothing=0)

from itertools import tee
def pairwise(iterable):
  a, b = tee(iterable)
  next(b, None)
  return zip(a, b)

class TestCounterSpace(unittest.TestCase):

  def test_1_solvingImprovesThings(self):
    for font in test_fonts:
      with self.subTest("Solving improves things for font "+font):
        c = spacers[font]
        c.key_pairs = ["HH","OO","HO","oo","nn","no"]
        c.options = { "h_center": 1000, "w_center": 1000, "h_top":1, "w_top": 1, "h_bottom":1, "w_bottom": 1, "top_strength":0.1, "bottom_strength":0.1, "center_strength":1 }
        def mse(string):
          found,good= c.test_string(string)
          return sum([(l-r)*(l-r) for l,r in zip(found,good)])

        dummy = mse("HOAVAnoon")

        c.determine_parameters()
        solved = mse("HOAVAnoon")
        self.assertLess(solved,dummy, "Solved MSE (%i) < dummy MSE (%i) for font %s " % (solved,dummy,font))

  def test_2_noCatastrophicFailures(self):
    for font in test_fonts:
        c = spacers[font]
        upem = c.font.face.units_per_EM
        for l,r in pairwise("HAMBURGEFONSIVhamburgefonsiv"):
          with self.subTest("Catastrophic failure test %s%s for font %s" % (l,r,font)):
            found = c.space(l,r)
            good = c.font.pair_distance(l,r) / c.font.scale_factor
            self.assertLess(abs(found-good), 60 * (upem/1024), "Catastrophic failure: %s%s (%i != %i)" % (l,r,found,good))

if __name__ == '__main__':
    unittest.main()