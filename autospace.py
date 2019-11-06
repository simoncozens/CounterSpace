from CounterSpace import CounterSpace
import string
import sys
import os

from fontTools.ttLib import TTFont

c = CounterSpace(sys.argv[1],serif_smoothing=0)
filename, file_extension = os.path.splitext(sys.argv[1])
spaced_filename = "%s-autospaced%s" % (filename,file_extension)

ttfont = TTFont(c.font.filename)
if not "glyf" in ttfont:
    print("Sorry, currently only supports truetype fonts. :-(")
    sys.exit(1)

def set_sidebearings(g,new_lsb,new_rsb):
    old_width, old_lsb = ttfont["hmtx"].metrics[g]
    old_rsb = old_width - max([f[0] for f in ttfont["glyf"][g].coordinates])
    ink_width = old_width - (old_lsb+old_rsb)
    ttfont["hmtx"].metrics[g] = (new_lsb+ink_width+new_rsb, new_lsb)
    ttfont["glyf"][g].coordinates -= (old_lsb-new_lsb,0)

print("Determining parameters...")
c.determine_parameters()

print("Spacing...")
lsbs = {}
rsbs = {}
for g in string.ascii_uppercase:
    lsbs[g], rsbs[g] = c.derive_sidebearings(g)
    print("%s LSB = %i, RSB = %i" % (g,lsbs[g],rsbs[g]))
    set_sidebearings(g,lsbs[g],rsbs[g])

print("\nKerning...")
for l in string.ascii_uppercase:
    for r in string.ascii_uppercase:
        print(l+r, end="", flush=True)
        desiredspace = c.space(l,r)
        currentspace = rsbs[l] + lsbs[r]
        kernvalue = desiredspace - currentspace
        if abs(kernvalue) > 5:
            print("("+str(kernvalue)+")", end="", flush=True)
            ttfont["kern"].kernTables[0][l,r] = kernvalue
        print(" ", end="", flush=True)

print("\nSaving "+spaced_filename)
ttfont.save(spaced_filename)
