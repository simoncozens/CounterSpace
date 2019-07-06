# coding: utf-8
import numpy as np
from tensorfont import Font,GlyphRendering
import scipy
import string
from fontTools.ttLib import TTFont

class CounterSpace:
    def __init__(self, filename,
        bare_minimum = 30,
        absolute_maximum = 500,
        serif_smoothing = 2,
        descend_into_counters = 150,
        centrality = 1900,
        top_strength = 50,
        italic_angle = 0,
        factor = 3,
        magic_number = 34):
        """
        To begin using CounterSpace, create a new `Counterspace` object by passing in the
OpenType font filename, and the following keyword parameters:

* `bare_minimum`: Minimum ink-to-ink distance. Default is 30 units. Increase this if "VV" is too close.
* `serif_smoothing`: Default is 0. Amount of blurring applied. Increase to 20 or so if you have prominent serifs.
* `descend_into_counters`: Default is 150 units. How far to measure into the counters. Decrease this if "OO" is too close.
* `centrality`: Default is 3000. Controls the vertical "spread" of light poured into counters.
* `top_strength`: Default is 50. Difference in strength between light from above and light from below. Alter if "rt" is too close.
* `italic_angle`: Default is 0 degrees.
    """
        self.filename = filename
        self.font = Font(self.filename, magic_number * factor)
        self.bare_minimum = bare_minimum * self.font.scale_factor
        self.serif_smoothing = serif_smoothing
        self.descend_into_counters = descend_into_counters * self.font.scale_factor
        self.centrality = centrality * self.font.scale_factor
        self.top_strength = top_strength
        self.italic_angle = italic_angle
        self.absolute_maximum = int(absolute_maximum * self.font.scale_factor)

        self.box_height = self.font.full_height_px
        self.box_width = int(75 * factor) # int(self.font.glyph("m").ink_width * 1.5)
        if self.box_width % 2 == 1:
            self.box_width = self.box_width + 1

        self.theta = italic_angle * np.pi/180
        self.alpha = (90 - italic_angle) * np.pi/180

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

        if serif_smoothing > 0:
            a = np.log(1.5*np.pi)/(serif_smoothing*(1+np.abs(self.theta)))
            lim = max(np.log(2*np.pi)/a, 1.)
            self.kernel = -np.sin(np.exp(-a*fx)) * np.where(fx>-lim, 1, 0) * a**2 * np.exp(-(fy/serif_smoothing)**2/2.)
            self.kernel *= self.kernel > 0
        else:
            self.kernel = None

    def counters(self, glyph):
        if glyph in self._counters: return self._counters[glyph]
        fg = self.font.glyph(glyph)
        self._counters[glyph] = fg.as_matrix(normalize=True).with_padding_to_constant_box_width(self.box_width).mask_ink_to_edge()
        return self._counters[glyph]

    def lshifted_counter(self, glyph, amount):
        if (glyph,amount) in self._lshifted_counters: return self._lshifted_counters[(glyph,amount)]
        _, left_counter = self.counters(glyph)
        c = scipy.ndimage.shift(left_counter, (0,amount), mode="nearest")
        c = GlyphRendering.init_from_numpy(glyph, c > 0.5)
        #Diagonize
        edge = c.left_contour(cutoff=0.5,max_depth=-1)
        oldedge = np.array(edge)
        for i in range(1,self.box_height-1):
            if edge[i] < edge[i-1]:
                oldedge[i] = edge[i]
                edge[i] = edge[i-1]-1
                c[i,oldedge[i]:edge[i]] = 0
        self._lshifted_counters[(glyph,amount)] = c
        return self._lshifted_counters[(glyph,amount)]

    def rshifted_counter(self,glyph,amount):
        if (glyph,amount) in self._rshifted_counters: return self._rshifted_counters[(glyph,amount)]
        right_counter,_ = self.counters(glyph)
        c = scipy.ndimage.shift(right_counter, (0,amount), mode="nearest")
        c = GlyphRendering.init_from_numpy(glyph, c > 0.5)
        #Diagonize
        edge = self.box_width - c.right_contour(cutoff=0.5,max_depth=-1)
        oldedge = np.array(edge)
        for i in range(1,self.box_height-1):
            if edge[i] > edge[i-1] and edge[i-1] > 0:
                oldedge[i] = edge[i]
                edge[i] = edge[i-1]+1
                c[i,edge[i]:oldedge[i]] = 0

        self._rshifted_counters[(glyph,amount)] = c
        return self._rshifted_counters[(glyph,amount)]

    def reference_pair(self,l,r):
        reference = "HH"
        if l in string.ascii_lowercase and r in string.ascii_lowercase:
            reference = "nn"
        if l in string.ascii_uppercase and r in string.ascii_lowercase:
            reference = "nn"
        if l in string.ascii_lowercase and r in string.ascii_uppercase:
            reference = "nn"
        return reference

    def pair_area(self, l,r,dist = None,reference=None):
        """Measure the area of the counter-space between two glyphs, set at
        a given distance. If the distance is got provided, then it is taken
        from the font's metrics. The glyphs are masked to the height of the
        reference pair."""
        f = self.font
        if dist is None:
            dist = f.pair_distance(l,r)
        if reference is None:
            reference = self.reference_pair(l,r)
        if (l,r,dist) in self._pair_areas:
            return self._pair_areas[(l,r,dist)]

        sigmas_top    = (self.descend_into_counters, self.centrality)
        sigmas_bottom = (self.descend_into_counters, self.centrality)

        lref, rref = [f.glyph(r) for r in reference]
        reftop = min(lref.tsb,rref.tsb)
        refbottom = min(lref.tsb+lref.ink_height, rref.tsb+rref.ink_height)

        shift_l, shift_r = f.shift_distances(l,r,dist)
        # This mask ensures we only care about the area "between" the
        # glyphs, and don't get into e.g. interior counters of "PP"
        l_shifted = self.lshifted_counter(l,shift_l)
        r_shifted = self.rshifted_counter(r,shift_r)
        ink_mask =  ~( (l_shifted<0.5) | (r_shifted<0.5))
        ink_mask[0:reftop,:] = 0
        ink_mask[refbottom:,:] = 0

        # If the light was from the middle, this is where it would be
        union = np.array(((l_shifted + r_shifted) * ink_mask) > 0)
        y_center, x_center = scipy.ndimage.measurements.center_of_mass(union)
        if np.isnan(y_center) or np.isnan(y_center): return np.sum(union)

        # But it might be coming from elsewhere, because of the italic angle
        top_x = int((x_center) + (y_center) / np.tan(self.alpha))
        bottom_x = int((x_center) - (self.box_height-y_center) / np.tan(self.alpha))
        top_y = 0
        bottom_y = self.box_height

        union = union > 0
        if not self.kernel is None:
            union = scipy.signal.convolve(union,self.kernel,mode="same")
        # print("Union after relu:", np.sum(union))

        # Now shine two lights from top and bottom
        toplight = self.gaussian(top_x,top_y,sigmas_top[0],sigmas_top[1],self.theta)
        # print(np.sum(toplight))
        bottomlight = self.gaussian(bottom_x,bottom_y,sigmas_bottom[0],sigmas_bottom[1],self.theta)
        # print(np.sum(bottomlight))
        union = union * ( self.top_strength * toplight + bottomlight )
        # print("Total light:", np.sum( self.top_strength * toplight + bottomlight ))
        self._pair_areas[(l,r,dist)] = np.sum(union)
        return self._pair_areas[(l,r,dist)]

    def space(self, l, r):
        reference = self.reference_pair(l,r)
        u_good = self.pair_area(reference[0],reference[1], reference=reference)
        mid = self.font.minimum_ink_distance(l, r)
        rv = None
        peak = -1
        peak_idx = -1
        goneover = False

        for n in range(-int(mid+self.bare_minimum),self.absolute_maximum,1):
            u = self.pair_area(l,r,dist=n, reference=reference)
            if u > u_good:
                rv = n
                goneover = True
                break
            if u > peak:
                peak = u
                peak_idx = n
        if rv is None:
            return peak_idx
        return int(rv / self.font.scale_factor)

    def derive_sidebearings(self, g, keyglyph = None):
        if keyglyph is None:
            keyglyph = self.reference_pair(g,g)[0]
        keyspace = self.space(keyglyph,keyglyph) // 2
        lsb = self.space(keyglyph,g) - keyspace
        rsb = self.space(g,keyglyph) - keyspace
        return(lsb,rsb)

    def fill_caches(self):
        for g in string.ascii_letters:
            self.counters(g)
            print(g)
            for n in range(-10,20):
                self.lshifted_counter(g,n)
                self.rshifted_counter(g,n)

if __name__ == '__main__':
    c = CounterSpace("OpenSans-Regular.ttf")
    print(np.sum(c.rshifted_counter("t",0)))
    print(c.pair_area("H","H"))
    print("TH", c.space("T","H"))
    print("HT", c.space("H","T"))
    # for g in string.ascii_letters:
    #     print(g, c.derive_sidebearings(g))
