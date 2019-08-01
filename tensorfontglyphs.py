
# wget https://files.pythonhosted.org/packages/ad/e3/7c8234b15137d2886bbbc3e9a7c83aae851b8cb1e3cf1c3210bdcce56b98/scikit_image-0.14.3-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
# wget https://files.pythonhosted.org/packages/26/6d/b55e412b5ae437dad6efe102b1a5bdefce4290543bbef78462a7a2037a1e/Pillow-6.1.0-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
# wget https://files.pythonhosted.org/packages/f2/16/c66bd67f34b8cd2964c2e9914401a27f8cb50398e8cf06ac6e65d80a2c6d/PyWavelets-1.0.3-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl

# sudo /usr/bin/easy_install scikit-image<0.15 numpy 
import numpy as np
from AppKit import NSBitmapImageRep, NSGraphicsContext, NSCalibratedWhiteColorSpace, NSPNGFileType,NSColor,NSBezierPath,NSMakeRect,NSAffineTransform
import math

from skimage.transform import resize
from skimage.util import pad
from skimage import filters

from scipy import ndimage
import scipy

from itertools import tee

safe_glyphs = set([
  "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
  "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
   ])

safe_glyphs_l = set([
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
])  

safe_glyphs_r = set([
  "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
  "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
])


class Font(object):
  """The `Font` module is your entry point for using Tensorfont.
  Use this to load up a font and begin exploring it.
  """

  def __init__(self, master, x_height_in_px):
    self.master = master

    # Set size by rendering /x and dividing by its height
    x_height_at_em = master.xHeight
    self.scale_factor = x_height_in_px / x_height_at_em

    self.ascender = self.master.ascender
    self.ascender_px = int(self.master.ascender * self.scale_factor)
    """The font's ascender height, in font units and pixels."""

    self.descender = self.master.descender
    self.descender_px = int(self.master.descender * self.scale_factor)
    """The font's descender height, in font units and pixels (usually negative)."""

    self.full_height = self.ascender - self.descender
    self.full_height_px = self.ascender_px - self.descender_px
    """The font's full (descender + ascender) height, in font units and pixels."""

    self.baseline_ratio = 1 - (self.ascender) / self.full_height
    """The ascender-to-descender ratio."""

    self.glyphcache = {}
    self.kernreader = None

  def get_xheight(self):
    return self.master.x_height

  def glyph(self, g):
    """Access a glyph by name. Returns a `Glyph` object."""
    if g in self.glyphcache: return self.glyphcache[g]
    self.glyphcache[g] = Glyph(self,g)
    return self.glyphcache[g]

  @property
  def m_width(self):
    """The width of the 'm' glyph, in font units."""
    return self.glyph("m").width

  @property
  def x_height(self):
    """The height of the 'x' glyph, in font units."""
    return self.glyph("x").height

  def pair_kerning(self, left, right):
    """The kerning between two glyphs (specified by name), in font units."""
    k1 = self.master.font.kerningForPair(self.master.id, left,right)
    if k1 < 1e10: return k1 * self.scale_factor
    # Some other stuff
    return 0

  def pair_distance(self, left, right, with_kerning=True):
    """The ink distance between two named glyphs, in font units.
    This is formed by adding the right sidebearing of the left glyph to the left sidebearing
    of the right glyph, plus a kerning correction. To turn off kerning, use `with_kerning=False`."""
    distance = self.glyph(left).rsb + self.glyph(right).lsb
    if with_kerning:
      distance = distance + self.pair_kerning(left, right)
    return distance

  def minimum_ink_distance(self,left,right):
    """The distance, in pixels, between the ink of the left glyph and the ink of the right glyph, when
    sidebearings are discarded. For many pairs, this will be zero, as the shapes bump up against
    each other (consider "nn" and "oo"). However, pairs like "VA" and "xT" will have a large
    minimum ink distance."""
    right_of_l = self.glyph(left).as_matrix().right_contour()
    left_of_r  = self.glyph(right).as_matrix().left_contour()
    return np.min(right_of_l + left_of_r)

  def maximum_ink_distance(self,left,right):
    """The maximum distance, in pixels, between the ink of the left glyph and the ink of the right glyph, when
    sidebearings are discarded. In other words, the size of the "hole" in the glyph (LV has a large hole)."""
    right_of_l = self.glyph(left).as_matrix().right_contour(max_depth = -1)
    left_of_r  = self.glyph(right).as_matrix().left_contour(max_depth = -1)
    return np.max(right_of_l + left_of_r)

  def shift_distances(self,l,r,dist):
    """Returns two distances, for which the left glyph matrix and the right glyph matrix
    should be translated such that, when the translations are done, the pair is set at a
    distance `dist` pixels apart.

    (Inputs `l` and `r` are glyph names, not `GlyphRendering` objects.)
    """
    sample_distance = dist + self.minimum_ink_distance(l,r)
    sample_distance_left = np.ceil(sample_distance / 2.0)
    sample_distance_right = np.floor(sample_distance / 2.0)
    total_ink_width = self.glyph(l).ink_width + self.glyph(r).ink_width
    ink_width_left = np.floor(total_ink_width / 4.0)
    ink_width_right = np.ceil(total_ink_width / 4.0)
    total_width_at_minimum_ink_distance = total_ink_width - self.minimum_ink_distance(l, r)
    left_translation = (-(np.ceil(total_width_at_minimum_ink_distance/2.0) + sample_distance_left) - (-ink_width_left))
    right_translation = ((np.floor(total_width_at_minimum_ink_distance/2.0) + sample_distance_right) - ink_width_right)
    return left_translation,right_translation

  def set_string(self, s, pair_distance_dict = {}):
    """Returns a matrix containing a representation of the given string. If a dictionary
    is passed to `pair_distance_dict`, then each pair name `(l,r)` will be looked up
    in the directionary and the result will be used as a distance *in pixel units* at
    which to set the pair. If no entry is found or no dictionary is passed, then the font
    will be queried for the appropriate distance.

    Hint: If you want to use glyph names which are not single characters, then pass an
    *array* of glyph names instead of a string."""
    def pairwise(iterable):
      a, b = tee(iterable)
      next(b, None)
      return zip(a, b)
    image = self.glyph(s[0]).as_matrix()
    for l,r in pairwise(s):
      newimage = self.glyph(r).as_matrix()
      if (l,r) in pair_distance_dict:
        dist = pair_distance_dict[(l,r)]
      else:
        dist = self.pair_distance(l,r)
      image = image.impose(newimage,int(dist))
    return image


class Glyph(object):
  """A representation of a glyph and its metrics."""
  def __init__(self, font, g):
    self.font = font
    self.master = font.master

    self.name = g
    """The name of the glyph."""

    self.gsglyph = self.master.font.glyphs[g]
    self.layer   = self.gsglyph.layers[font.master.id]
    if len(self.layer.components) > 0:
      self.layer = self.layer.copyDecomposedLayer()

    self.ink_width = self.layer.bounds.size.width * self.font.scale_factor
    self.ink_height= self.layer.bounds.size.height * self.font.scale_factor
    self.width     = self.layer.width * self.font.scale_factor
    """The width of the glyph in font units (including sidebearings)."""
    self.lsb       = self.layer.LSB * self.font.scale_factor
    """The left sidebearing in font units."""
    self.rsb       = self.layer.RSB * self.font.scale_factor
    """The right sidebearing in font units."""
    self.tsb       = self.layer.TSB * self.font.scale_factor
    """The top sidebearing (distance from ascender to ink top) in font units."""

  def as_matrix(self, normalize = False, binarize = False):
    """Renders the glyph as a matrix. By default, the matrix values are integer pixel greyscale values
    in the range 0 to 255, but they can be normalized or turned into binary values with the
    appropriate keyword arguments. The matrix is returned as a `GlyphRendering` object which
    can be further manipulated."""
    box_height = int(self.font.full_height_px)
    box_width  = int(self.ink_width)

    b = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(None,box_width,box_height,8,1,False,False,NSCalibratedWhiteColorSpace, 0,0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(b)
    assert(ctx)
    NSGraphicsContext.setCurrentContext_(ctx)

    NSColor.whiteColor().setFill()
    p2 = NSBezierPath.bezierPath()
    p2.appendBezierPath_(self.layer.completeBezierPath)
    t = NSAffineTransform.transform()
    t.translateXBy_yBy_(-self.lsb,-self.font.descender * self.font.scale_factor)
    t.scaleBy_(self.font.scale_factor)
    p2.transformUsingAffineTransform_(t)
    p2.fill()

    png = b.representationUsingType_properties_(NSPNGFileType,None)
    png.writeToFile_atomically_("/tmp/foo.png", False)
    Z = np.array(b.bitmapData())
    box_width_up = Z.shape[0]/box_height
    Z = Z.reshape((box_height,box_width_up))[0:box_height,0:box_width]

    if normalize or binarize:
      Z = Z / 255.0
    if binarize:
      Z = Z.astype(int)
    return GlyphRendering.init_from_numpy(self,Z)

class GlyphRendering(np.ndarray):
  @classmethod
  def init_from_numpy(self, glyph, matrix):
    s = GlyphRendering(matrix.shape)
    s[:] = matrix
    s._glyph = glyph
    return s

  def with_padding(self, left_padding, right_padding):
    """Returns a new `GlyphRendering` object, left and right zero-padding to the glyph image."""
    padding = ((0,0),(left_padding, right_padding))
    padded = pad(self, padding, "constant")
    return GlyphRendering.init_from_numpy(self._glyph, padded)

  def with_padding_to_constant_box_width(self, box_width):
    padding_width = (box_width - int(self._glyph.ink_width)) / 2.0
    padding = ((0, 0), (int(np.ceil(padding_width)), int(np.floor(padding_width))))
    padded = pad(self, padding, "constant")
    return GlyphRendering.init_from_numpy(self._glyph, padded)

  def with_sidebearings(self):
    """Returns a new `GlyphRendering` object, extending the image to add the
    glyph's sidebearings. If the sidebearings are negative, the matrix
    will be trimmed appropriately."""
    lsb = self._glyph.lsb
    rsb = self._glyph.rsb
    matrix = self
    if lsb < 0:
        matrix = GlyphRendering.init_from_numpy(self._glyph,self[:,-lsb:])
        lsb = 0
    if rsb < 0:
        matrix = GlyphRendering.init_from_numpy(self._glyph,self[:,:rsb])
        rsb = 0
    return matrix.with_padding(lsb,rsb)

  def mask_to_x_height(self):
    """Returns a new `GlyphRendering` object, cropping the glyph image
    from the baseline to the x-height. (Assuming that the input `GlyphRendering` is full height.)"""
    f = self._glyph.font
    baseline = int(f.full_height + f.descender)
    top = int(baseline - f.x_height)
    cropped = self[top:baseline,:]
    return GlyphRendering.init_from_numpy(self._glyph, cropped)

  def crop_descender(self):
    """Returns a new `GlyphRendering` object, cropping the glyph image
    from the baseline to the ascender. (Assuming that the input `GlyphRendering` is full height.)"""
    f = self._glyph.font
    baseline = int(f.full_height + f.descender)
    cropped = self[:baseline,:]
    return GlyphRendering.init_from_numpy(self._glyph, cropped)

  def scale_to_height(self, height):
    """Returns a new `GlyphRendering` object, scaling the glyph image to the
    given height. (The new width is calculated proportionally.)"""
    new_width = int(self.shape[1] * height / self.shape[0])
    return GlyphRendering.init_from_numpy(self._glyph, resize(self, (height, new_width), mode="constant"))

  def left_contour(self, cutoff = 30, max_depth = 10000):
    """Returns the left contour of the matrix; ie, the 'sidebearing array' from the
    edge of the matrix to the leftmost ink pixel. If no ink is found at a given
    scanline, the value of max_depth is used instead."""
    contour = np.argmax(self > cutoff, axis=1) + max_depth * (np.max(self, axis=1) <= cutoff)
    return np.array(contour)

  def right_contour(self, cutoff = 30, max_depth = 10000):
    """Returns the right contour of the matrix; ie, the 'sidebearing array' from the
    edge of the matrix to the rightmost ink pixel. If no ink is found at a given
    scanline, the value of max_depth is used instead."""
    pixels = np.fliplr(self)
    contour = np.argmax(pixels > cutoff, axis=1) + max_depth * (np.max(pixels, axis=1) <= cutoff)
    return np.array(contour)

  def apply_flexible_distance_kernel(self, strength):
    """Transforms the matrix by applying a flexible distance kernel, with given strength."""
    transformed = 1. - np.clip(strength-ndimage.distance_transform_edt(np.logical_not(self)),0,strength)
    return GlyphRendering.init_from_numpy(self._glyph,transformed)

  def gradients(self):
    """Returns a pair of images representing the horizontal and vertical gradients."""
    return filters.sobel_h(self), filters.sobel_v(self)

  def impose(self, other, distance=0):
    """Returns a new `GlyphRendering` object made up of two `GlyphRendering` objects
    placed side by side at the given distance."""
    if self.shape[0] != other.shape[0]:
      raise ValueError("heights don't match in impose")
    extension = distance + other.shape[1]
    extended = self.with_padding(0,extension)
    extended[:,self.shape[1]+distance:self.shape[1]+extension] += other
    return extended

  def set_at_distance(self,other,distance=0):
    """Similar to `impose` but returns a pair of `GlyphRendering` objects separately, padded at the correct distance."""
    s2, o2 = self.with_padding(0, other.shape[1] + distance), other.with_padding(self.shape[1]+distance, 0)
    return s2, o2

  def mask_ink_to_edge(self):
    """Returns two `GlyphRendering` objects representing the left and right "edges" of the glyph:
    the first has positive values in the space between the left-hand contour and the left edge of the matrix
    and zero values elsewhere, and the second has positive values between the right-hand contour and
    the right edge of the matrix and zero values elsewhere. In other words this gives you the
    "white" at the edge of the glyph, without any interior counters."""
    def last_nonzero(arr, axis, invalid_val=-1):
        mask = arr > 5/255.0
        val = arr.shape[axis] - np.flip(mask, axis=axis).argmax(axis=axis) - 1
        return np.where(mask.any(axis=axis), val, invalid_val)

    def first_zero(arr, axis, invalid_val=-1):
        mask = arr < 5/255.0
        val = mask.argmax(axis=axis) - 1
        return np.where(mask.any(axis=axis), val, invalid_val)

    def left_counter(image):
        lcounter = 1 - image
        lnonz = first_zero(lcounter,1)
        for x in range(lnonz.shape[0]): lcounter[x,1+lnonz[x]:] = 0
        lcounter -= np.min(lcounter)
        for x in range(lnonz.shape[0]): lcounter[x,lnonz[x]:] = 0
        return lcounter

    def right_counter(image):
        rcounter = np.flip(image,axis=1)
        rcounter = left_counter(rcounter)
        rcounter = np.flip(rcounter,axis=1)
        return rcounter

    return [GlyphRendering.init_from_numpy(self._glyph,x) for x in [left_counter(self), right_counter(self)]]
