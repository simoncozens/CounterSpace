# coding: utf-8
from __future__ import print_function

import numpy as np
import sys

if sys.version_info[0] == 3:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve

try:
    import GlyphsApp
    from tensorfontglyphs import Font,GlyphRendering
except Exception as e:
    from tensorfont import Font,GlyphRendering

import scipy
import string
from scipy.signal import convolve

class CounterSpace:
    def __init__(self, file,
        bare_minimum = 50,
        absolute_maximum = 500,
        serif_smoothing = 2,
        key_pairs = ["HH","OO","HO","OH","EE","AV"],
        x_height_in_pixels = 90,
        ):
        """
        To begin using CounterSpace, create a new `Counterspace` object by passing in the
OpenType font filename, and the following keyword parameters:

* `bare_minimum`: Minimum ink-to-ink distance. Default is 30 units. Increase this if "VV" is too close.
* `serif_smoothing`: Default is 0. Amount of blurring applied. Increase to 20 or so if you have prominent serifs.
    """
        self.filename = file
        self.font = Font(self.filename, x_height_in_pixels)
        self.bare_minimum = bare_minimum * self.font.scale_factor
        self.serif_smoothing = serif_smoothing
        self.absolute_maximum = int(absolute_maximum * self.font.scale_factor)
        self.key_pairs = key_pairs
        self.options = None

        self.box_height = self.font.full_height_px
        self.box_width = int(x_height_in_pixels * 10/3)
        if self.box_width % 2 == 1:
            self.box_width = self.box_width + 1

        self.theta = self.font.italic_angle * np.pi/180
        self.alpha = (90 - self.font.italic_angle) * np.pi/180

        # Various caches
        self._counters = {}
        self._lshifted_counters = {}
        self._rshifted_counters = {}
        self._pair_areas = {}

        hh = self.box_height / 2.
        bw = self.box_width / 2.
        fy, fx = np.mgrid[-hh:hh, -bw:bw] + 1.
        self.fx = fx
        self.fy = fy

        def gaussian(center_x, center_y, width_x, width_y, rotation):
            """Returns a gaussian function with the given parameters"""
            # print("Gaussian with parameters",center_x, center_y, width_x, width_y, rotation)
            width_x = float(width_x)
            width_y = float(width_y)
            center_x = self.box_width/2 - center_x
            center_y = self.box_height/2 - (self.box_height - center_y)
            center_x = center_x * np.cos(rotation) - center_y * np.sin(rotation)
            center_y = center_x * np.sin(rotation) + center_y * np.cos(rotation)

            xp = fx * np.cos(rotation) - fy * np.sin(rotation)
            yp = fx * np.sin(rotation) + fy * np.cos(rotation)
            g = np.exp(
                -(((center_x-xp)/width_x)**2+
                  ((center_y-yp)/width_y)**2)/2.)
            return np.flip(g,axis=1)
        self.gaussian = gaussian

        self.set_serif_smoothing(serif_smoothing)

    def set_serif_smoothing(self, serif_smoothing):
        self.serif_smoothing = serif_smoothing
        if serif_smoothing > 0:
            a = np.log(1.5*np.pi)/(serif_smoothing*(1+np.abs(self.theta)))
            lim = max(np.log(2*np.pi)/a, 1.)
            self.kernel = -np.sin(np.exp(-a*self.fx)) * np.where(self.fx>-lim, 1, 0) * a**2 * np.exp(-(self.fy/serif_smoothing)**2/2.)
            self.kernel *= self.kernel > 0
        else:
            self.kernel = None
        self._lshifted_counters = {}
        self._rshifted_counters = {}

    def counters(self, glyph):
        if glyph in self._counters: return self._counters[glyph]
        fg = self.font.glyph(glyph)
        self._counters[glyph] = fg.as_matrix(normalize=True).with_padding_to_constant_box_width(self.box_width).mask_ink_to_edge()
        return self._counters[glyph]

    def lshifted_counter(self, glyph, amount,reftop, refbottom):
        if (glyph,amount,reftop,refbottom) in self._lshifted_counters: return self._lshifted_counters[(glyph,amount,reftop,refbottom)]
        fg = self.font.glyph(glyph).as_matrix()
        conc = 0
        if fg.discontinuity(contour="right") > 0:
            conc = 1-fg.right_face()
        if self.kernel is not None:
            fg = GlyphRendering.init_from_numpy(fg._glyph,convolve(fg,self.kernel,mode="same") > 250)
        padded = fg.with_padding_to_constant_box_width(self.box_width)
        padded[0:reftop,:]   = 0
        padded[refbottom:,:] = 0
        padded = padded.reduce_concavity(conc)
        c = scipy.ndimage.shift(padded, (0,amount), mode="nearest")
        l,r = GlyphRendering.init_from_numpy(glyph, c).mask_ink_to_edge()
        r = (r>0).astype(np.uint8)
        self._lshifted_counters[(glyph,amount,reftop,refbottom)] = r
        return r

    def rshifted_counter(self,glyph,amount,reftop,refbottom):
        if (glyph,amount,reftop,refbottom) in self._rshifted_counters: return self._rshifted_counters[(glyph,amount,reftop,refbottom)]
        fg = self.font.glyph(glyph).as_matrix()
        conc = 0
        if fg.discontinuity(contour="left") > 0:
            conc = 1-fg.left_face()
        if self.kernel is not None:
            fg = GlyphRendering.init_from_numpy(fg._glyph,convolve(fg,self.kernel,mode="same") > 250)
        padded = fg.with_padding_to_constant_box_width(self.box_width)
        padded[0:reftop,:]   = 0
        padded[refbottom:,:] = 0
        padded = padded.reduce_concavity(conc)
        c = scipy.ndimage.shift(padded, (0,amount), mode="nearest")
        l,r = GlyphRendering.init_from_numpy(glyph, c).mask_ink_to_edge()
        l = (l>0).astype(np.uint8)
        self._rshifted_counters[(glyph,amount,reftop,refbottom)] = l
        return l

    def reference_pair(self,l,r):
        reference = "HH"
        if l in string.ascii_lowercase and r in string.ascii_lowercase:
            reference = "nn"
        if l in string.ascii_uppercase and r in string.ascii_lowercase:
            reference = "nn"
        if l in string.ascii_lowercase and r in string.ascii_uppercase:
            reference = "nn"
        return reference

    def pair_area(self, l, r, options, dist = None,reference=None):
        """Measure the area of the counter-space between two glyphs, set at
        a given distance. If the distance is got provided, then it is taken
        from the font's metrics. The glyphs are masked to the height of the
        reference pair."""
        f = self.font
        if dist is None:
            dist = f.pair_distance(l,r)
        if reference is None:
            reference = self.reference_pair(l,r)
        shift_l, shift_r = f.shift_distances(l,r,dist)

        lref, rref = [f.glyph(ref) for ref in reference]
        reftop = int(min(lref.tsb,rref.tsb))
        refbottom = int(min(lref.tsb+lref.ink_height, rref.tsb+rref.ink_height))
        reftop = reftop + self.serif_smoothing
        refbottom = refbottom - self.serif_smoothing
        sigmas_top    = (options["w_top"], options["h_top"])
        sigmas_bottom = (options["w_bottom"], options["h_bottom"])
        sigmas_center = (options["w_center"], options["h_center"])

        top_strength = options["top_strength"]
        bottom_strength = options["bottom_strength"]
        center_strength = options["center_strength"]

        redgeofl = (self.box_width - f.glyph(l).ink_width) / 2.0 + f.glyph(l).ink_width + shift_l
        ledgeofr = self.box_width-((self.box_width - f.glyph(r).ink_width) / 2.0 + f.glyph(r).ink_width) + shift_r
        center = (redgeofl + ledgeofr)/2 - f.minimum_ink_distance(l, r) / 2
        midline = (reftop+refbottom)/2 - self.box_height/2

        # This mask ensures we only care about the area "between" the
        # glyphs, and don't get into e.g. interior counters of "PP"
        l_shifted = self.lshifted_counter(l,shift_l,reftop,refbottom)
        r_shifted = self.rshifted_counter(r,shift_r,reftop,refbottom)
        ink_mask =  (l_shifted > 0) & (r_shifted > 0)
        ink_mask[0:reftop,:] = 0
        ink_mask[refbottom:,:] = 0

        # If the light was from the middle, this is where it would be
        union = np.array(((l_shifted + r_shifted) * ink_mask) > 0)
        y_center, x_center = scipy.ndimage.measurements.center_of_mass(union)
        if np.isnan(y_center) or np.isnan(y_center): return union
        top_x = int((x_center) + (y_center) / np.tan(self.alpha))
        bottom_x = int((x_center) - (self.box_height-y_center) / np.tan(self.alpha))
        top_y = 0
        bottom_y = self.box_height

        # Blur the countershape slightly
        union = union > 0
        # Now shine two lights from top and bottom
        toplight    = self.gaussian(top_x,top_y,sigmas_top[0],sigmas_top[1],self.theta)
        bottomlight = self.gaussian(bottom_x,bottom_y,sigmas_bottom[0],sigmas_bottom[1],self.theta)
        centerlight = self.gaussian(x_center,y_center,sigmas_center[0],sigmas_center[1],self.theta)

        # XXX - this "shadowing" idea doesn't quite work
        
        # fnonz = False
        # for i in range(reftop+1,refbottom):
        #     if fnonz:
        #         toplight[i,:] = toplight[i,:] * (toplight[i-1,:] > 0) * (union[i,:] > 0)
        #     else:
        #         if np.any(toplight[i,:] > 0):
        #             fnonz = True
        # fnonz = False
        # for i in range(refbottom-1,reftop,-1):
        #     if fnonz:
        #         bottomlight[i,:] = bottomlight[i,:] * (bottomlight[i+1,:] > 0) * (union[i,:] > 0)
        #     else:
        #         if np.any(toplight[i,:] > 0):
        #             fnonz = True

        #     #     print("Total light:", np.sum( top_strength * toplight + bottomlight ))
        union =  centerlight * center_strength * union + union * bottomlight * bottom_strength + union * ( top_strength * toplight)
        return union

    def determine_parameters(self, callback = None):
        bounds_for = {
            "w_center": (5,25),
            "h_center": (10,50),
            "w_top": (5,25),
            "h_top": (10,50),
            "w_bottom": (5,50),
            "h_bottom": (10,50),
            "center_strength": (1,5),
            "top_strength": (0.05,1),
            "bottom_strength": (0.05,1),
        }
        def solve_for(variables, strings, options):
            reference = strings.pop(0)
            bounds = [bounds_for[v] for v in variables]
            guess =  [options[v] for v in variables]
            def comparator(o):
                for ix,var in enumerate(variables):
                    options[var] = o[ix]
                HH = np.sum(self.pair_area(reference[0],reference[1],options))
                err = []
                for s in strings:
                    val = np.sum(self.pair_area(s[0],s[1],options))
                    err.append( ( val - HH) / HH )
                err = np.sum(np.array(err) ** 2)
                if callback:
                    callback(err)
                return err
            result = scipy.optimize.minimize(comparator,guess,
                method="TNC",
                bounds=bounds,
                options={
                    # 'maxfev': 200
                    'xtol': 0.01,
                    'eta': 0.8
                },
                )
            for ix,var in enumerate(variables):
                options[var] = result.x[ix]
            return options

        options = solve_for(
            variables = ["h_center","w_center","center_strength","h_top","w_top","top_strength","h_bottom","w_bottom","bottom_strength"],
            strings = self.key_pairs,
            options = {
                "w_top": 15,
                "w_bottom": 15,
                "h_top": 15,
                "h_bottom": 15,
                "h_center": 15,
                "w_center": 30,
                "top_strength": 0.5,
                "bottom_strength": 0.8,
                "center_strength": 2
            }
        )
        self.options = options
        return options

    def space(self, l, r):
        if not self.options:
            raise ValueError("You need to run .determine_parameters() or set self.options manually")
        reference = self.reference_pair(l,r)
        u_good = np.sum(self.pair_area(reference[0],reference[1], self.options, reference=reference))
        mid = self.font.minimum_ink_distance(l, r)
        rv = None
        peak = -1
        peak_idx = -1
        goneover = False

        for n in range(-int(mid)+int(self.bare_minimum),self.absolute_maximum,1):
            u = np.sum(self.pair_area(l,r,self.options,dist=n, reference=reference))
            if u > u_good:
                rv = n
                goneover = True
                break
            if u > peak:
                peak = u
                peak_idx = n
        if rv is None:
            return int(peak_idx / self.font.scale_factor)
        return int(rv / self.font.scale_factor)

    def derive_sidebearings(self, g, keyglyph = None):
        if keyglyph is None:
            keyglyph = self.reference_pair(g,g)[0]
        keyspace = self.space(keyglyph,keyglyph) // 2
        lsb = self.space(keyglyph,g) - keyspace
        rsb = self.space(g,keyglyph) - keyspace
        return(lsb,rsb)

    @classmethod
    def get_sample_font(self, name):
        sample_fonts = {
            "CrimsonRoman.otf": "https://github.com/skosch/Crimson/blob/master/Desktop%20Fonts/OTF/Crimson-Roman.otf?raw=true",
            "Tinos-Italic.ttf": "https://github.com/jenskutilek/free-fonts/raw/master/Tinos/TTF/Tinos-Italic.ttf",
            "PTSerif-Italic.ttf": "https://github.com/divspace/pt-serif/raw/master/fonts/pt-serif/pt-serif-italic.ttf",
            "Crimson-SemiboldItalic.otf": "https://github.com/skosch/Crimson/raw/master/Desktop%20Fonts/OTF/Crimson-SemiboldItalic.otf",
            "OpenSans-Regular.ttf": "https://github.com/google/fonts/blob/master/apache/opensans/OpenSans-Regular.ttf"
        }
        if not (name in sample_fonts):
            print("%s not known; sample fonts available are: %s" % (name, ", ".join(sample_fonts.keys())))
            return
        import os.path
        if not os.path.isfile(name):
            urlretrieve(sample_fonts[name], name)
            print("Downloaded %s" % name)

if __name__ == '__main__':
    c = CounterSpace("OpenSans-Regular.ttf",serif_smoothing=0)
    print("Determining parameters", end="")
    print(c.determine_parameters(callback = lambda x: print(".",end="",flush=True)))
    pdd = {}

    def compare(s):
        global pdd
        found = c.space(s[0],s[1]) * c.font.scale_factor
        good = c.font.pair_distance(s[0],s[1])
        pdd[(s[0],s[1])] = found
        if abs(found-good) > 5:
            ok="!!!"
        else:
            ok=""
        print("%s: pred=%i true=%i %s" % (s,found/c.font.scale_factor,good/c.font.scale_factor, ok))

    from itertools import tee
    def pairwise(iterable):
      a, b = tee(iterable)
      next(b, None)
      return zip(a, b)

    def fill_pdd(s):
      for l,r in pairwise(s):
        if not (l,r) in pdd: compare((l,r))

    for s in ["XX","DV","VF","FA","AV","tx", "VV","no","ga","LH"]:
        compare(s)
