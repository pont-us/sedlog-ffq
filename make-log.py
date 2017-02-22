#!/usr/bin/python
# -*- coding: UTF-8

import math, random, cairo, csv
from math import pi, radians
import symb

FONT_NAME = 'NimbusSanLCon'

pdf_output = True
def pt(mm):
    return (mm / 25.4) * 72

# Scale & Page only used for currents

class Scale:

    def __init__(self, src_min, src_max, dst_min, dst_max):
        self.src_min = src_min
        self.src_max = src_max
        self.dst_min = dst_min
        self.dst_max = dst_max
        self.src_range = src_max - src_min
        self.dst_range = dst_max - dst_min
        self.scale_factor = self.dst_range/self.src_range
    
    def length(self, src):
        return self.scale_factor * src

    def pos(self, src):
        return self.dst_min + self.scale_factor * (src-self.src_min)

class Page:
    def __init__(self, s_top, s_bot, p_top, p_bot):
        self.s_top = s_top
        self.s_bot = s_bot
        self.p_top = p_top
        self.p_bot = p_bot
        self.scale = Scale(s_top, s_bot, p_top, p_bot)

class LogSettings:

    def __init__(self):
        self.fmn_name_offset = -8 # vertical offset of formation name
        self.stagger_pmag = False # whether to stagger pmag sites
        self.pmag_stagger = 12 # distance by which to stagger pmag sites
        self.glc_voffset = 20 # vertical offset for g symbols
        self.glc_int = 20 # don't draw g closer than this unless changing
        self.glc_int_2 = 1 # don't draw g closer than this even if changing
        self.symb_int = 12 # don't draw other symbols closer than this
        self.special_pmag_offsets = {'D1':0, 'D2':1}
        self.all_drill_sites = True # if False, only draw valid sites
        self.decs_incs_list = None # put table here to draw decs & incs
        self.ages = None
        self.currents = False

log_settings = LogSettings()

class LogState:

    def __init__(self):
        self.pmag_stagger = 0
        self.last_burrow = -1e6
        self.last_calc = -1e6
        self.last_wood = -1e6

log_state = LogState()

liths = {}
liths['sst'] = symb.sand_pattern(pdf_output) # cairo.SolidPattern(0.7,0.7,0.7)
liths['sist'] = symb.silt_pattern(pdf_output)
burrow_pattern = symb.burrow_pattern(pdf_output)
grain_sizes = ['clay', 'silt', 'vfs'] #, 'fs', 'ms']
grain_sizes_print = ['clay', 'silt', 'v. f. sand']
grain_index = {}
magsus_scale = 50000
for i in range(0, len(grain_sizes)):
    grain_index[grain_sizes[i]] = i

hz_pos_mm = {
    'scale' : 7,
    'fmn'   : 9,
    'lith'  : 16,
    'magsus': 65,
    'drill' : 80,
    'colour': 90,
    'notes' : 105,
    'drill2': 102,
    'dec'   : 118,
    'inc'   : 129,
    'dec_g' : 95,
    'inc_g' : 124
}

lith_width = 45

fmns_paged = (
 ('Fairfield Greensand Member', 500, 740),
 ('Saddle Hill Siltstone Member', 740, 1060),
 ('Steele Greensand Member', 1060, 1300),
 ('Quarries Siltstone Member', 1400, 2100),
 ('Quarries SM', 2100, 2130),
 ('Abbotsford Formation', 2130, 2400),
 ('Abbotsford Formation', 2400, 2700),
 ('Abbotsford Formation', 2700, 3000)
)

fmns_summary = (
 ('Fairfield GM', 500, 740),
 ('Saddle Hill SM', 740, 1060),
 ('Steele GM', 1060, 1300),
 ('Quarries Siltstone Member', 1300, 2130),
 ('Abbotsford Formation', 2130, 3000),
)

valid_sites = set(('k5 k3 k2 k1 j6 j3 i3 h6 h5 h4 h3 h1 f8 d1 f7 f6 d3 f4 '+\
                  'd2 f3 f2 f1 c4 e4 c3 e3 c2 e2 c1 b3 b2').split())

pmag_blocks = {
  ('K5','K3','K2','K1') : 2880,
  ('H6','H5','H4','H3') : 2310,
  ('F8','D1','F7') : 1780,
  ('D2', 'F3') : 1520,
  ('C4','E4','C3','E3','C2','E2', 'C1', 'B3') : 1015
}

decinc_graph_breaks = set(['K5', 'F8','C4'])

hz_pos = {}
for v in hz_pos_mm.keys():
    hz_pos[v] = pt(hz_pos_mm[v])

def ffloat(s):
    if s == '': return 0.
    return float(s)

last_glc_height = None

def align_text(ctx, x, y, text, horiz = 'l', vert = 'b'):
    extents = ctx.text_extents(text)
    w = extents[2]
    h = extents[3]
    if horiz=='l': x_pos = x
    elif horiz=='r': x_pos = x-w
    else: x_pos = x-w/2
    if vert=='t': y_pos = y
    elif vert=='b': y_pos = y+h
    else: y_pos = y+h/2
    ctx.move_to(x_pos, y_pos)
    ctx.show_text(text)

def write_lines(ctx, x_pos, y_pos, spacing, lines):
    for i in range(len(lines)):
        ctx.move_to(x_pos, y_pos + i * spacing)
        ctx.show_text(lines[i])

class Datum:

    def __init__(self, prm):
        self.bot = float(prm['U'])
        self.thick = float(prm['th'])
        self.gs = (prm['grain'])
        self.lith = (prm['lith'])
        self.glc = ffloat(prm['glc%'])
        self.drill = prm['drill']
        self.burrow = prm['burrows']
        self.acid = prm['acid']
        self.fossil = prm['fossils']
        self.colour = prm['colour']
        self.magsus = prm['ms']
        self.contact = prm['cont']
        self.notes = prm['notes']
        self.label_offs = ffloat(prm['label-offs'])

    def top(self):
        return self.bot + self.thick

    def draw_lith(self, ctx, bot, top, xoffs, width_b, width_t):
        ctx.move_to(xoffs, bot)
        ctx.set_line_width(.5)
        ctx.rel_line_to(width_b, 0)
        ctx.line_to(xoffs+width_t, top)
        ctx.line_to(xoffs, top)
        ctx.close_path()
        ctx.set_source(liths[self.lith])
        ctx.fill_preserve()
        if (self.lith=='sist'): ctx.set_source(burrow_pattern)
        ctx.fill()
        ctx.set_line_width(.5)
        ctx.set_source_rgb(0,0,0)
        ctx.move_to(xoffs, bot)
        ctx.line_to(xoffs, top)
        ctx.stroke()
        ctx.move_to(xoffs+width_b, bot)
        ctx.line_to(xoffs+width_t, top)
        ctx.stroke()

    def draw_noexp(self, ctx, top, height, xoffs, width):
        ctx.set_line_width(.5)
        ctx.rectangle(xoffs, top, width, height)
        ctx.move_to(xoffs, top)
        ctx.rel_line_to(width, height)
        ctx.rel_move_to(0, -height)
        ctx.rel_line_to(-width, height)
        ctx.set_source_rgb(0,0,0)
        ctx.stroke()
        ctx.fill()

    def draw(self, height, ctx, scale, next, yoffs):
        d = self
        xoffs = hz_pos['lith']
        top = (height-(self.bot+self.thick)+yoffs)*scale
        bot = (height-self.bot+yoffs)*scale
        width = 100
        global log_state
        if self.thick > 0:
            if self.lith != 'ne':
                width_b = (1+grain_index[self.gs])*lith_width
                if next!=None and next.lith != '' and next.lith != 'ne':
                    width_t = (1+grain_index[next.gs])*lith_width
                else: width_t = width_b
                self.draw_lith(ctx, bot, top, xoffs, width_b, width_t)
                width = min(width_t, width_b)
            else:
                self.draw_noexp(ctx, top, self.thick*scale, xoffs, width)
        if top<log_state.last_calc: log_state.last_calc = -1e6
        if self.acid != '' and float(self.acid)>2 and \
                top-log_state.last_calc > log_settings.symb_int:
            symb.calc(ctx, xoffs+50, top+4, 4)
            if float(self.acid)>3:
                symb.calc(ctx, xoffs+20, top+6, 4)
            log_state.last_calc = top
        if top<log_state.last_burrow: log_state.last_burrow = -1e6
        if self.burrow != '' and top-log_state.last_burrow > log_settings.symb_int:
            symb.burrow(ctx, xoffs+10, top+6, 4, self.burrow.find('py')>-1)
            log_state.last_burrow = top
        if top<log_state.last_wood: log_state.last_wood = -1e6
        if self.fossil != '' and top-log_state.last_wood > log_settings.symb_int:
            symb.wood(ctx, xoffs+30, top+6, 4)
            log_state.last_wood = top
        if self.colour != '' and hz_pos['colour'] != None:
            ctx.move_to(hz_pos['colour'], bot+3)
            ctx.show_text(self.colour)
        if self.contact != '':
            symb.irregular_contact(ctx, xoffs, bot, width_b)
        if self.notes != '' and hz_pos['notes'] != None:
            write_lines(ctx, hz_pos['notes'], bot+3, 8,
                        self.notes.split('|'))
            #ctx.move_to(hz_pos['notes'], bot+3)
            #ctx.show_text(self.notes)
        if self.magsus != '':
            ms = float(self.magsus) * magsus_scale
            ctx.rectangle(hz_pos['magsus'], top-4, ms, 8)
            ctx.set_source_rgb(.8,.8,.8)
            ctx.fill_preserve()
            ctx.set_source_rgb(0,0,0)
            ctx.set_line_width(0.5)
            ctx.stroke()
        do_glc = True
        global last_glc_height
        if next != None and last_glc_height != None:
            # a boolean mare's nest :-(
            if (self.bot > (last_glc_height - log_settings.glc_int) and
                next.glc == self.glc):
                do_glc = False
            if (self.bot > (last_glc_height - log_settings.glc_int_2)):
                do_glc = False
            if self.bot > last_glc_height: do_glc = True
        #print self.bot, self.glc, last_glc_height, do_glc
        if do_glc:
            symb.glc(ctx, xoffs, top+log_settings.glc_voffset, width, self.glc)
            if last_glc_height==None: last_glc_height = self.bot
            else: last_glc_height = min(self.bot, last_glc_height)
        if self.drill != '':
            drill_xpos = hz_pos['drill']
            if log_settings.stagger_pmag:
                if self.drill in log_settings.special_pmag_offsets:
                    log_state.pmag_stagger = \
                        log_settings.special_pmag_offsets[self.drill]
                drill_xpos += log_state.pmag_stagger * log_settings.pmag_stagger
                log_state.pmag_stagger = (log_state.pmag_stagger + 1) % 3
            if (log_settings.all_drill_sites or 
                self.drill.lower() in valid_sites):
                ctx.move_to(drill_xpos, bot+3-self.label_offs)
                ctx.set_source_rgb(0,0,0)
                ctx.show_text(self.drill)

def read_csv(filename):
    f = open(filename, 'rb')
    r = csv.reader(f)
    headers = r.next()
    data = []
    for values in r:
        data.append(Datum(dict(zip(headers,values))))
    f.close()
    return data

def read_csv_to_dicts(filename):
    f = open(filename, 'rb')
    r = csv.reader(f)
    headers = r.next()
    data = {}
    for values in r:
        data[values[0]] = (dict(zip(headers,values)))
    f.close()
    return data

def read_csv_to_list(filename):
    f = open(filename, 'rb')
    r = csv.reader(f)
    headers = r.next()
    data = []
    for values in r:
        data.append((dict(zip(headers,values))))
    f.close()
    return data

def draw_axis(height, ctx, bot, top, interval, scale, offset):
    x_offs = hz_pos['scale']
    ctx.move_to(x_offs, (height-bot)*scale)
    ctx.line_to(x_offs, (height-top)*scale)
    ctx.set_line_width(1)
    ctx.set_source_rgb(0,0,0)
    ctx.stroke()
    nticks = int(round((top-bot)/interval + 1))
    for i in range(0, nticks):
        y = (height-(bot + i * interval))*scale
        ctx.move_to(x_offs, y)
        ctx.rel_line_to(-4, 0)
        ctx.stroke()
        ctx.move_to(x_offs-18, y+3.5)
        ctx.show_text(str(int((offset + i * interval)/100)))

def read_magsus(filename):
    ms = []
    f = open(filename, 'r')
    for line in f.readlines():
        parts = line.strip().split('\t')
        if len(parts)<2: continue
        height, magsus = parts
        ms.append((float(height), float(magsus)))
    return ms

def draw_magsus(ctx, height, bot_clip, top_clip, scale, yoffs, ms_values):
    ctx.set_line_width(0.5)
    x_offs = hz_pos['magsus']
    first = True
    #ctx.move_to(x_offs, (height+yoffs-bot_clip)*scale)
    #ctx.line_to(x_offs, (height+yoffs-top_clip)*scale)
    scale_lines = 5
    real_width = 40.
    dist_per_line = real_width / (scale_lines-1)
    for i in range(0, scale_lines):
        dist = i * dist_per_line
        ctx.move_to(x_offs+dist, (height+yoffs-bot_clip)*scale)
        ctx.line_to(x_offs+dist, (height+yoffs-top_clip)*scale)
    ctx.stroke()
    y = 0
    first_y = 0
    for (h, ms) in ms_values:
        if h<bot_clip or h>top_clip: continue
        y = (height-h+yoffs)*scale
        x = x_offs + ms * magsus_scale
        if first:
            ctx.move_to(x_offs, y)
            first_y = y
            # ctx.move_to(x, y)
            first = False
        ctx.line_to(x, y)
    ctx.line_to(x_offs, y)
    ctx.line_to(x_offs, first_y)
    ctx.close_path
    ctx.set_source_rgb(.8,.8,.8)
    ctx.fill_preserve()
    ctx.set_source_rgb(0,0,0)
    ctx.stroke()

def draw_formation(ctx, height, bot_clip, top_clip, scale, yoffs, name, bot, top):
    if top>top_clip or bot<bot_clip: return
    ctx.set_line_width(0.5)
    y = (height-top+yoffs)*scale
    h = (top-bot)*scale
    ctx.rectangle(hz_pos['fmn'], y, 15, h)
    ctx.set_source_rgb(0,0,0)
    ctx.stroke()
    ctx.move_to(hz_pos['fmn']+11, y+h+log_settings.fmn_name_offset)
    ctx.save()
    ctx.rotate(-pi/2.)
    ctx.show_text(name)
    ctx.restore()

def draw_decsincs_table(ctx, height, bot_clip, top_clip, scale, yoffs):
    def write_decinc(datum, y):
        align_text(ctx, hz_pos['drill2'], y, datum['site'], 'l', 'c')
        align_text(ctx, hz_pos['dec'], y, datum['dec'], 'r', 'c')
        align_text(ctx, hz_pos['inc'], y, datum['inc'], 'r', 'c')
    for site, datum in log_settings.decs_incs.items():
        in_block = False
        for pmag_block in pmag_blocks.keys():
            if site in pmag_block: in_block = True
        h = float(datum['height'])
        y = (height-h+yoffs)*scale
        if not in_block:
            write_decinc(datum, y)
    for pmag_block, h0 in pmag_blocks.items():
        y0 = (height-h0+yoffs)*scale
        for i in range(len(pmag_block)):
            y = y0 + i*10
            site = pmag_block[i]
            write_decinc(log_settings.decs_incs[site], y)

def draw_decsincs_graph(ctx, height, bot_clip, top_clip, scale, yoffs):
    def draw_param(param_name, p_scale, grid_lines):
        x_offs = hz_pos[param_name+'_g']
        ctx.set_line_width(0.5)
        for grid_line in grid_lines:
            dist = x_offs + grid_line * p_scale
            ctx.move_to(dist, (height+yoffs-bot_clip)*scale)
            ctx.line_to(dist, (height+yoffs-top_clip)*scale)
            ctx.stroke()
        for i in (0, len(grid_lines)-1):
            align_text(ctx, x_offs + grid_lines[i] * p_scale,
                       (height+yoffs-top_clip)*scale-2, 
                       str(grid_lines[i]), 'c', 't')
        ctx.set_source_rgb(0.,0.,0.)
        for style in (0,1): # lines, dots
            for datum in log_settings.decs_incs_list:
                h = float(datum['height'])
                param = float(datum[param_name])
                y = (height-h+yoffs)*scale
                x = x_offs + param * p_scale
                if style==1:
                    ctx.set_line_width(0.5)
                    ctx.arc(x, y, 1.5, 0, 2*pi)
                    ctx.stroke()
                    # ctx.fill()
                if style==0:
                    if (datum['site'] in decinc_graph_breaks): ctx.move_to(x, y)
                    else: ctx.line_to(x,y)
            if style==0:
                ctx.set_line_width(1.0)
                ctx.stroke()
    draw_param('dec', 0.16, (0, 90, 180, 270, 360))
    draw_param('inc', 0.4, (0, 30, 60, 90))

def draw_header(ctx, ypos):
    global log_settings
    ctx.move_to(hz_pos['scale']-20, ypos)
    ctx.show_text('h (m)')
    for i in range(0, len(grain_sizes)+1):
        ctx.move_to(hz_pos['lith'] + lith_width * i, ypos)
        ctx.rel_line_to(0, -12)
        ctx.set_source_rgb(0,0,0)
        ctx.stroke()
        if i>0:
            x, y = (hz_pos['lith'] + lith_width * i - 4, ypos)
            align_text(ctx, x, y, grain_sizes_print[i-1], 'r', 't')
    ctx.move_to(hz_pos['drill']+6, ypos)
    ctx.show_text('pmag')
    ctx.move_to(hz_pos['magsus'], ypos-3)
    ms_x = hz_pos['magsus']
    ctx.show_text('mag. sus.')
    for i in range(0,5):
        align_text(ctx, ms_x + 10*i, ypos+7, str(2*i), 'c', 't')
    if hz_pos['colour']:
        ctx.move_to(hz_pos['colour'], ypos)
        ctx.show_text('colour')
    if log_settings.decs_incs_list != None:
        align_text(ctx, hz_pos['dec_g']+180.*.16, ypos, 'declination', 'c', 't')
        align_text(ctx, hz_pos['inc_g']+45.*.4, ypos, 'inclination', 'c', 't')
    if log_settings.currents:
        align_text(ctx, 400, ypos, 'current', 'l', 't')

def draw_direction(ctx, x, y, radius, direction):
    ctx.save()
    ctx.arc(x, y, radius, 0, 2*pi)
    ctx.translate(x,y)
    ctx.rotate(radians(direction))
    r2 = radius * 0.95
    ctx.move_to(0, r2*.9)
    ctx.line_to(0, -r2*.9)
    ctx.stroke()
    for i in range(2):
        if i==1: ctx.rotate(pi)
        ctx.move_to(0, r2)
        ctx.line_to(-r2*.2, r2*.8)
        ctx.line_to(r2*.2, r2*.8)
        ctx.close_path()
        ctx.fill()
    ctx.restore()

def draw_currents(ctx, x_pos, page, currents):
    for (bottom, top, direction) in currents:
        print bottom
        ctx.move_to(x_pos, page.scale.pos(bottom))
        ctx.line_to(x_pos+4, page.scale.pos(bottom))
        ctx.line_to(x_pos+4, page.scale.pos(top))
        ctx.line_to(x_pos, page.scale.pos(top))
        ctx.stroke()
        if (direction == None):
            write_lines(ctx, x_pos+8, page.scale.pos((bottom+top)/2)-12,
                        10, 'No current detected'.split())
        elif (isinstance(direction, str)):
            write_lines(ctx, x_pos+8, page.scale.pos((bottom+top)/2)-12,
                        10, direction.split('|'))
        else:
            draw_direction(ctx, x_pos+17, page.scale.pos((bottom+top)/2), 10,
                           direction)

def draw_annotation(ctx, x_pos, page, annotation):
    (height, text) = annotation
    print height, text
    width = 135
    ctx.set_line_width(2.)
    ctx.set_source_rgb(.3,.3,.3)
    ctx.move_to(x_pos, page.scale.pos(height))
    ctx.line_to(x_pos+width, page.scale.pos(height))
    ctx.stroke()
    ctx.set_source_rgb(0,0,0)
    align_text(ctx, x_pos + width + 2, page.scale.pos(height), text, 'l', 'c')

def draw_page(bot_clip, top_clip, ds, ms_values, scale, formations,
              legend = None, filename = None, current_data = None,
              annotation = None):
    global last_glc_height, log_settings
    last_glc_height = None
    height = top_clip - bot_clip
    top_margin = 24
    bot_margin = 5
    total_height_pt = scale * height + top_margin + bot_margin
    if filename==None: filename = 'output/ffq%04d' % bot_clip
    if (pdf_output):
        surface = cairo.PDFSurface(filename+'.pdf', pt(160), total_height_pt)
    else:
        surface = cairo.SVGSurface(filename+'.svg', pt(160), total_height_pt)
    ctx = cairo.Context(surface)
    ctx.select_font_face(FONT_NAME)
    
    if (annotation != None): draw_annotation(ctx, 20, annotation[0], annotation[1])

    draw_magsus(ctx, height + top_margin/scale, bot_clip, top_clip, scale,
                bot_clip, ms_values)

    for i in range(0, len(ds)):
        if i>0: above = ds[i-1]
        else: above = None
        d = ds[i]
        if d.bot >= bot_clip and d.bot + d.thick <= top_clip:
            ds[i].draw(height + top_margin/scale, ctx, scale, above, bot_clip)
    
    draw_axis(height + top_margin/scale, ctx, 0., height, 100., scale, bot_clip)
    draw_header(ctx, top_margin-10)
    if log_settings.decs_incs_list != None:
        draw_decsincs_graph(ctx, height + top_margin/scale,
                            bot_clip, top_clip, scale,
                            bot_clip)
    for (name, bot, top) in formations:
        draw_formation(ctx, height + top_margin/scale, bot_clip, top_clip, scale,
                bot_clip, name, bot, top)
    if current_data != None:
        page, currents = current_data
        draw_currents(ctx, 400, page, currents)
    if legend != None:
        draw_legend(ctx, *legend)
    surface.finish()

def draw_pattern_box(ctx, x, y, w, h, pattern, text):
    ctx.rectangle(x, y, w, h)
    ctx.set_source(pattern)
    ctx.fill_preserve()
    ctx.set_source_rgb(0,0,0)
    ctx.set_line_width(0.5)
    ctx.stroke()
    ctx.move_to(x+w+4, y+h/2+2)
    ctx.show_text(text)

def legend_glc(ctx, x, y):
    ctx.move_to(x, y)
    ctx.show_text('Glaucony content')
    concs = (1, 6, 21, 51, 81)
    labels = ('<5%', '5–20%', '20–50%', '50–80%', '>80%')
    for i in range(0, len(concs)):
        symb.glc(ctx, x, y+(i+1)*12, 30, concs[i])
        ctx.move_to(x+35, y+(i+1)*12)
        ctx.show_text(labels[i])
        i += 1

def legend_features(ctx, xo, yo):
    step = 12
    scale = 4
    x, y = xo, yo
    def label(text):
        ctx.move_to(x+15, y+2)
        ctx.show_text(text)
    symb.wood(ctx, x, y, scale)
    label('Fossil wood')
    y += step
    symb.burrow(ctx, x, y, scale)
    label('Distinct burrow')
    y += step
    symb.burrow(ctx, x, y, scale, True)
    label('Pyritized burrow')
    y += step
    symb.calc(ctx, x, y, scale)
    label('Calcareous')
    y += step

def draw_legend(ctx, xo, yo):
    ctx.save()
    ctx.translate(xo, yo)
    ctx.select_font_face(FONT_NAME)
    draw_pattern_box(ctx, 10, 10, 50, 36, liths['sist'], 'Siltstone')
    draw_pattern_box(ctx, 10, 50, 50, 36, liths['sst'], 'Sandstone')
    draw_pattern_box(ctx, 10, 90, 50, 36, burrow_pattern, 'Burrow mottling')
    symb.irregular_contact(ctx, 10, 140, 50)
    ctx.move_to(64, 142)
    ctx.show_text('Irregular/burrowed contact')
    legend_glc(ctx, 10, 170)
    legend_features(ctx, 10, 250)
    ctx.restore()

def draw_all():
    ds = read_csv('input-data/sed-data.csv')
    ms_values = read_magsus('input-data/ms.txt')
    intervals = (2100, 2400, 2700, 3000)
    for i in range(0, len(intervals)-1):
        draw_page(intervals[i], intervals[i+1], ds, ms_values, 2, fmns_paged)
    intervals = (500, 1300, 2100)
    for i in range(0, len(intervals)-1):
        legend = None
        if (i==0): legend = (270, 320)
        draw_page(intervals[i], intervals[i+1], ds, ms_values, 0.75,
                  fmns_paged, legend=legend)
    global glc_int, log_settings, hz_pos, pdf_output
    log_settings.fmn_name_offset = -2
    log_settings.stagger_pmag = True
    log_settings.glc_voffset = 10
    log_settings.glc_int = 49
    log_settings.glc_int_2 = 31
    hz_pos['colour'] = None
    hz_pos['notes'] = None
    draw_page(500, 3000, ds, ms_values, 0.24, fmns_summary,
              legend=(280,220), filename='output/ffq-log-entire');
    log_settings.all_drill_sites = False
    hz_pos_new = {}
    for col, pos in hz_pos.items():
        if col != 'scale' and pos != None: pos += 34
        hz_pos_new[col] = pos
    # hz_pos = hz_pos_new # uncomment to shunt columns rightward
    #log_settings.decs_incs_dict = read_csv_to_dicts('site-incdec.csv')
    log_settings.decs_incs_list = read_csv_to_list('input-data/site-incdec.csv')
    currents = ((5.5, 7.45, 354.8), (7.55, 8.95, 137.3), (9.05, 11.95, 272.8),
                (12.05, 29.5, 'Inverse|AMS|fabric'))
    page = Page(29.5, 5.5, pt(12), pt(215))
    log_settings.currents = True
    draw_page(500, 3000, ds, ms_values, 0.24, fmns_summary,
              filename='output/ffq-log-entire-2', current_data=(page, currents),
              annotation = (page, (21.2, 'K-Pg')));

draw_all()
