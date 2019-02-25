#!/usr/bin/python3

# This file is part of sedlog-ffq, Copyright 2009, 2017, 2019 Pontus Lurcock
# (pont at talvi dot net) and released under the MIT license:

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import cairocffi as cairo
import random
from math import pi

def calc(c, x, y, s):
    c.move_to(x-s, y-s/2)
    c.rel_line_to(s*2, 0)
    c.rel_move_to(-s, 0)
    c.rel_line_to(0, s)
    c.rel_move_to(-s, 0)
    c.rel_line_to(2*s, 0)
    c.set_line_width(1)
    c.set_source_rgb(0,0,0)
    c.stroke()

def glc(c, x, y, width, pc):
    c.save()
    c.select_font_face('NimbusSanLCon',cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD)
    c.set_source_rgb(0,0,0)
    gs = 0
    limits = (0, 5, 20, 50, 80)
    for limit in limits:
        if pc>limit: gs += 1
    for i in range(1,gs+1):
        c.move_to(x + i * (width/(gs+1)) - 3, y)
        c.show_text('g')
    c.restore()

def wood(c, x, y, s):
    c.move_to(x+s/2,y)
    c.arc(x, y, s/2, 0, 2*pi)
    c.move_to(x, y-s/2)
    c.rel_line_to(s*2, 0)
    c.arc(x+2*s, y, s/2, 3*pi/2, pi/2)
    c.rel_line_to(-s*2, 0)
    c.rel_move_to(0, s)
    c.close_path()
    c.set_source_rgb(1,1,1)
    c.fill_preserve()
    c.set_source_rgb(0,0,0)
    c.set_line_width(1)
    c.stroke()

def burrow(c, x, y, s, pyt=False):
    c.save()
    c.save()
    c.translate(x, y)
    c.scale(1., 2.)
    c.move_to(0,0)
    c.arc(0, 0, s/2, 0, 2*pi)
    c.restore()
    c.set_line_width(s/4.)
    c.set_source_rgb(1,1,1)
    c.fill_preserve()
    c.set_source_rgb(0,0,0)
    c.move_to(x-s, y)
    c.rel_line_to(s*2, 0)
    c.stroke()
    if pyt:
        c.move_to(x+s*0.8, y+s*0.7)
        c.select_font_face('NimbusSanLCon',cairo.FONT_SLANT_NORMAL,
                           cairo.FONT_WEIGHT_NORMAL)
        c.show_text('P')
    c.restore()

def silt_pattern():
    p_surface = \
        cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0, 0, 32, 8))
    ctx = cairo.Context(p_surface)
    ctx.set_line_width(.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    r = 0.5
    sc = 2
    yoffs = 1
    ctx.set_source_rgb(0,0,0)
    def dot(x, y):
        ctx.arc(x*sc, y*sc+yoffs, r, 0, 2*pi)
        ctx.fill()
    def hz_line(x0, x1, y):
        ctx.move_to(x0*sc, y*sc+yoffs)
        ctx.line_to(x1*sc, y*sc+yoffs)
        ctx.stroke()
    hz_line(0.2, 7.8, 1)
    hz_line(8.2, 15.8, 3)
    for x in 10, 12, 14: dot(x, 1)
    for x in 2, 4, 6: dot(x, 3)
    pattern = cairo.SurfacePattern(p_surface)
    pattern.set_extend(cairo.EXTEND_REPEAT)
    return pattern

def sand_pattern():
    p_surface = \
        cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0, 0, 36, 36))
    p_ctx = cairo.Context(p_surface)
    r = 0.5
    wiggle = 3
    sc = 3.6
    offs = 1.8
    random.seed(11)
    p_ctx.set_source_rgb(0,0,0)
    for x in range(0,10):
        for y in range(0,10):
            p_ctx.arc(offs+x*sc+random.random()*wiggle-wiggle/2,
                      offs+y*sc+random.random()*wiggle-wiggle/2,
                      r, 0, 2*pi)
            p_ctx.fill()
    # for x in range(0,2):
    #     for y in range(0,2):
    #         burrow(p_ctx, 4.5+x*18+random.random()*8.-8./2.,
    #                   9+y*18+random.random()*8.-8./2., 2)
    pattern = cairo.SurfacePattern(p_surface)
    pattern.set_extend(cairo.EXTEND_REPEAT)
    return pattern

def burrow_pattern():
    p_surface = \
        cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0, 0, 36, 36))
    ctx = cairo.Context(p_surface)
    random.seed(17)
    ctx.set_source_rgb(0,0,0)
    for x in range(0,4):
        for y in range(0,2):
            burrow(ctx, 4.5+x*24+random.random()*8,
                      9+y*36+random.random()*8+x*8, 2)
    pattern = cairo.SurfacePattern(p_surface)
    pattern.set_extend(cairo.EXTEND_REPEAT)
    return pattern

def irregular_contact(ctx, x, y, width):
    wave_w = 12
    wave_h = 3
    n_waves = width // wave_w + 1
    ctx.save()
    ctx.rectangle(x, y-wave_h-5, width, 2*(wave_h+5))
    ctx.clip()
    ctx.set_line_width(1.)
    ctx.move_to(x,y)
    for i in range(0, n_waves):
        ctx.rel_curve_to(0, -wave_h, wave_w, -wave_h, wave_w, 0)
        ctx.rel_curve_to(0, wave_h, wave_w, wave_h, wave_w, 0)
    ctx.stroke()
    ctx.restore()
