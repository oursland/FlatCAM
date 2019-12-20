##############################################################
# FlatCAM: 2D Post-processing for Manufacturing              #
# http://flatcam.org                                         #
# File Author: Matthieu Berthomé                             #
# Date: 5/26/2017                                            #
#                                                            #
# Correction & Adaptation for Berta CNC machine              #
# Date: 24/10/2019                                           #
#                                                            #
# MIT Licence                                                #
##############################################################

from FlatCAMPostProc import *


class Berta_CNC(FlatCAMPostProc):

    include_header = True
    coordinate_format = "%.*f"
    feedrate_format = '%.*f'

    def start_code(self, p):
        units = ' ' + str(p['units']).lower()
        coords_xy = p['xy_toolchange']
        gcode = ''

        xmin = '%.*f' % (p.coords_decimals, p['options']['xmin'])
        xmax = '%.*f' % (p.coords_decimals, p['options']['xmax'])
        ymin = '%.*f' % (p.coords_decimals, p['options']['ymin'])
        ymax = '%.*f' % (p.coords_decimals, p['options']['ymax'])

        if str(p['options']['type']) == 'Geometry':
            gcode += '(TOOL DIAMETER: ' + str(p['options']['tool_dia']) + units + ')\n'

        gcode += '(Feedrate: ' + str(p['feedrate']) + units + '/min' + ')\n'

        if str(p['options']['type']) == 'Geometry':
            gcode += '(Feedrate_Z: ' + str(p['z_feedrate']) + units + '/min' + ')\n'

        gcode += '(Feedrate rapids ' + str(p['feedrate_rapid']) + units + '/min' + ')\n' + '\n'
        gcode += '(Z_Cut: ' + str(p['z_cut']) + units + ')\n'

        if str(p['options']['type']) == 'Geometry':
            if p['multidepth'] is True:
                gcode += '(DepthPerCut: ' + str(p['z_depthpercut']) + units + ' <=>' + \
                         str(math.ceil(abs(p['z_cut']) / p['z_depthpercut'])) + ' passes' + ')\n'

        gcode += '(Z_Move: ' + str(p['z_move']) + units + ')\n'
        gcode += '(Z Toolchange: ' + str(p['z_toolchange']) + units + ')\n'

        if coords_xy is not None:
            gcode += '(X,Y Toolchange: ' + "%.*f, %.*f" % (p.decimals, coords_xy[0],
                                                           p.decimals, coords_xy[1]) + units + ')\n'
        else:
            gcode += '(X,Y Toolchange: ' + "None" + units + ')\n'

        gcode += '(Z Start: ' + str(p['startz']) + units + ')\n'
        gcode += '(Z End: ' + str(p['z_end']) + units + ')\n'
        gcode += '(Steps per circle: ' + str(p['steps_per_circle']) + ')\n'

        if str(p['options']['type']) == 'Excellon' or str(p['options']['type']) == 'Excellon Geometry':
            gcode += '(Preprocessor Excellon: ' + str(p['pp_excellon_name']) + ')\n' + '\n'
        else:
            gcode += '(Preprocessor Geometry: ' + str(p['pp_geometry_name']) + ')\n' + '\n'

        gcode += '(X range: ' + '{: >9s}'.format(xmin) + ' ... ' + '{: >9s}'.format(xmax) + ' ' + units + ')\n'
        gcode += '(Y range: ' + '{: >9s}'.format(ymin) + ' ... ' + '{: >9s}'.format(ymax) + ' ' + units + ')\n\n'

        gcode += '(Spindle Speed: %s RPM)\n' % str(p['spindlespeed'])

        gcode += (
            # This line allow you to sets the machine to METRIC / INCH in the GUI
            'G20\n' if p.units.upper() == 'IN' else 'G21\n') + '\n'
        #        gcode += 'G21\n' # This line sets the machine to METRIC ONLY
        #        gcode += 'G20\n' # This line sets the machine to INCH ONLY

        gcode += 'G90 G17 G91.1\n'
        gcode += 'G64 P0.03\n'
        gcode += 'M110\n'
        gcode += 'G54\n'
        gcode += 'G0\n'
        gcode += '(Berta)\n'
        gcode += 'G94\n'

        return gcode

    def startz_code(self, p):
        if p.startz is not None:
            return 'G00 Z' + self.coordinate_format % (p.coords_decimals, p.startz)
        else:
            return ''

    def lift_code(self, p):
        return 'G00 Z' + self.coordinate_format % (p.coords_decimals, p.z_move)

    def down_code(self, p):
        return 'G01 Z' + self.coordinate_format % (p.coords_decimals, p.z_cut)

    def toolchange_code(self, p):
        z_toolchange = p.z_toolchange
        toolchangexy = p.xy_toolchange
        f_plunge = p.f_plunge

        if toolchangexy is not None:
            x_toolchange = toolchangexy[0]
            y_toolchange = toolchangexy[1]
        else:
            x_toolchange = 0
            y_toolchange = 0

        no_drills = 1

        if int(p.tool) == 1 and p.startz is not None:
            z_toolchange = p.startz

        toolC_formatted = '%.*f' % (p.decimals, p.toolC)

        if str(p['options']['type']) == 'Excellon':
            for i in p['options']['Tools_in_use']:
                if i[0] == p.tool:
                    no_drills = i[2]

            if toolchangexy is not None:
                gcode = """
M5
G00 Z{z_toolchange}
G00 X{x_toolchange} Y{y_toolchange}                
T{tool}
M6
(MSG, Change to Tool Dia = {toolC} ||| Total drills for tool T{tool} = {t_drills})
M0
""".format(x_toolchange=self.coordinate_format % (p.coords_decimals, x_toolchange),
           y_toolchange=self.coordinate_format % (p.coords_decimals, y_toolchange),
           z_toolchange=self.coordinate_format % (p.coords_decimals, z_toolchange),
           tool=int(p.tool),
           t_drills=no_drills,
           toolC=toolC_formatted)
            else:
                gcode = """
M5       
G00 Z{z_toolchange}
T{tool}
M6
(MSG, Change to Tool Dia = {toolC} ||| Total drills for tool T{tool} = {t_drills})
M0""".format(z_toolchange=self.coordinate_format % (p.coords_decimals, z_toolchange),
             tool=int(p.tool),
             t_drills=no_drills,
             toolC=toolC_formatted)

            if f_plunge is True:
                gcode += '\nG00 Z%.*f' % (p.coords_decimals, p.z_move)
            return gcode

        else:
            if toolchangexy is not None:
                gcode = """
M5
G00 Z{z_toolchange}
G00 X{x_toolchange} Y{y_toolchange}
T{tool}
M6    
(MSG, Change to Tool Dia = {toolC})
M0""".format(x_toolchange=self.coordinate_format % (p.coords_decimals, x_toolchange),
             y_toolchange=self.coordinate_format % (p.coords_decimals, y_toolchange),
             z_toolchange=self.coordinate_format % (p.coords_decimals, z_toolchange),
             tool=int(p.tool),
             toolC=toolC_formatted)
            else:
                gcode = """
M5
G00 Z{z_toolchange}
T{tool}
M6    
(MSG, Change to Tool Dia = {toolC})
M0""".format(z_toolchange=self.coordinate_format % (p.coords_decimals, z_toolchange),
             tool=int(p.tool),
             toolC=toolC_formatted)

            if f_plunge is True:
                gcode += '\nG00 Z%.*f' % (p.coords_decimals, p.z_move)
            return gcode

    def up_to_zero_code(self, p):
        return 'G01 Z0'

    def position_code(self, p):
        return ('X' + self.coordinate_format + ' Y' + self.coordinate_format) % \
               (p.coords_decimals, p.x, p.coords_decimals, p.y)

    def rapid_code(self, p):
        return ('G00 ' + self.position_code(p)).format(**p)

    def linear_code(self, p):
        return ('G01 ' + self.position_code(p)).format(**p)

    def end_code(self, p):
        coords_xy = p['xy_toolchange']
        gcode = ('G00 Z' + self.feedrate_format % (p.fr_decimals, p.z_end) + "\n")

        if coords_xy is not None:
            gcode += 'G00 X{x} Y{y}'.format(x=coords_xy[0], y=coords_xy[1]) + "\n"

        gcode += '(Berta)\n'
        gcode += 'M111\n'
        gcode += 'M30\n'
        gcode += '(Berta)\n'
        return gcode

    def feedrate_code(self, p):
        return 'G01 F' + str(self.feedrate_format % (p.fr_decimals, p.feedrate))

    def z_feedrate_code(self, p):
        return 'G01 F' + str(self.feedrate_format % (p.fr_decimals, p.z_feedrate))

    def spindle_code(self, p):
        sdir = {'CW': 'M03', 'CCW': 'M04'}[p.spindledir]
        if p.spindlespeed:
            return '%s S%s' % (sdir, str(p.spindlespeed))
        else:
            return sdir

    def dwell_code(self, p):
        if p.dwelltime:
            return 'G4 P' + str(p.dwelltime)

    def spindle_stop_code(self, p):
        return 'M05'