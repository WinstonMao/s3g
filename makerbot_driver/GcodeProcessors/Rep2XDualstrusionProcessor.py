#Search through the Gcode for significant toolchanges. It then

from __future__ import absolute_import

import re

from . import Processor
import makerbot_driver

class Rep2XDualstrusionProcessor(Processor):

    def __init__(self):
        super(Rep2XDualstrusionProcessor, self).__init__()
        self.is_bundleable = True
        self.layer_start = re.compile("^\((Slice|<layer>) [0-9.]+.*\)")
        self.toolchange = re.compile("^M135 T([0-9])")
        self.MG_snort = re.compile("^G1 F([0-9.-]+) ([AB])([0-9.-]+) \(snort\)")
        self.MG_squirt = re.compile("^G1 F([0-9.-]+) ([AB])([0-9.-]+) \(squirt\)")
        self.SF_layer_end = re.compile("^\(</layer>\)")
        self.SF_snortsquirt = re.compile("^G1 E([0-9.-]+)")
        self.SF_feedrate = re.compile("^G1 F([0-9.-]+)")

        self.MG_anchor_end = re.compile("^G1 X([0-9.-]+) Y([0-9.-]+) Z([0-9.-]+) F([0-9.-]+) ([AB])([0-9.-]+) \(Anchor End\)")
        self.SF_anchor = re.compile("^G1 X([0-9.-]+) Y([0-9.-]+) Z([0-9.-]+) F([0-9.-]+) E([0-9.-]+)")
        self.SF_set_position_post_anchor = re.compile("^G92 E[0-9.-]+")

        self.retract_distance_mm = None
        self.return_distance_mm = None
        self.squirt_reduction = None
        self.snort_reduction = None

        self.MG_TOOLHEADS = ['A', 'B']

        self.slicer = None

    def process_gcode(self, gcode_in, outfile=None, profile=None, slicer=None):
        self.retract_distance_mm = profile.values["dualstrusion"][
            "retract_distance_mm"]
        self.squirt_reduction = profile.values["dualstrusion"][
            "squirt_reduce_mm"]
        self.squirt_feedrate = profile.values["dualstrusion"][
            "squirt_feedrate"]
        self.snort_feedrate = profile.values["dualstrusion"][
            "snort_feedrate"]

        self.slicer = slicer


        if(outfile != None):
            if(self.retract_distance_mm == 'NULL'):
            #if this value is null this process in not relevant, so return the input
                self.gcode_fp = open(gcode_in, 'r')
                self.output_fp = open(outfile, 'w+')
                for line in self.gcode_fp:
                    self.output_fp.write(line)
                self.gcode_fp.close()
                self.output_fp.close()
                return True
            else:
                return self.process_gcode_file(gcode_in, outfile)
        else:
            #TODO update/fix list input functionality
            if(isinstance(gcode_in, list)):
                raise NotImplementedError("List input not fully supported")
                if(self.retract_distance_mm == 'NULL'):
                #if this value is null this process in not relevant, so return the input
                    return gcode_in
                return self.process_gcode_list(gcode_in)
            else:
                return False


    def process_gcode_list(self, gcodes, callback=None):
    #TODO Update this to use the new functions
    #This processes gcode in the form of a list of gcodes, and the processed gcode is returned
        self.gcodes = gcodes
        self.max_index = (len(gcodes)-1)
        self.output = []
        self.last_tool = -1
        self.code_index = 0
        self.slicer = None

        while(self.code_index <= self.max_index):
            self.output.append(self.gcodes[self.code_index])
            self.match = re.match(self.toolchange, self.gcodes[self.code_index])
            if self.match is not None:
                if(self.last_tool == -1):
                    self.last_tool = self.match.group(1)
                elif(self.last_tool != self.match.group(1)):
                    #search backwards for the last snort
                    (snort_index,current_feedrate,current_position) = self.reverse_snort_search(is_GcodeFile=False)
                    #depending on the slicer emit a new snort using fixed feedrates and position
                    if(self.slicer == 'miracle_grue'):
                        self.new_feedrate = self.snort_feedrate
                        self.new_extruder_pos = current_position-self.retract_distance_mm
                        self.output[snort_index] = "G1 F%.3f A%.3f (snort)\n"%(self.new_feedrate,self.new_extruder_pos)
                    elif(self.slicer == 'skeinforge'):
                        self.new_feedrate = self.snort_feedrate
                        self.new_extruder_pos = current_position-self.retract_distance_mm
                        self.output[snort_index-1] = "G1 F.1%f\n" %(self.new_feedrate)
                        self.output[snort_index] = "G1 E.3%f\n" %(self.new_extruder_pos)
            self.code_index += 1
        return self.output


    def write_preprint_purge(self, isGcodeFile):
        pass

    def snort_inactive_tool(self, isGcodeFile):
    #This retracts the inactive tool at the start of a print
    #This does not support more than 2 extruders
        for line in self.gcode_fp:
            match = re.match(self.toolchange, line)
            if match is not None:

                self.last_tool = match.group(1)
                tool = not (int(match.group(1))) #get the other tool assuming that there aren't more than 2 extruders

                self.output_fp.write("M135 T%i\n"%(tool))
                self.output_fp.write("G92 %s%.2f\n"%(self.MG_TOOLHEADS[tool],self.retract_distance_mm))
                if(self.slicer == 'miracle_grue'):
                    self.output_fp.write("G1 F%.2f %s%.2f\n"%(self.snort_feedrate,self.MG_TOOLHEADS[tool],0))
                elif(self.slicer == 'skeinforge'):
                   self.output_fp.write("G1 F%.2f\nG1 E%.2f\n"%(self.snort_feedrate,0))

                self.output_fp.write(line)
                self.output_fp.flush()
                return

    def squirt_inactive_tool(self, tool, current_pos, isGcodeFile, doToolchange = False):
        if(doToolchange):
            self.output_fp.write("M135 T%i\n"%int(tool))
            self.output_fp.write("G92 %s%.2f\n"%(self.MG_TOOLHEADS[int(tool)], 0))
        if(self.slicer == 'miracle_grue'):
            self.output_fp.write("G1 F%.2f %s%.2f\n"%(self.squirt_feedrate, self.MG_TOOLHEADS[int(tool)], self.retract_distance_mm))
            #attach a G92 after a inactive tool squirt to reset position to zero
            #This only occurs at the start and end of a print
            self.output_fp.write("G92 %s%.2f\n"%(self.MG_TOOLHEADS[int(tool)], 0))
        elif(self.slicer == 'skeinforge'):
            self.output_fp.write("G1 F%.2f\nG1 E%.2f\n"%(self.squirt_feedrate, self.retract_distance_mm))
            self.output_fp.write("G92 %s%.2f\n"%(self.MG_TOOLHEADS[int(tool)], 0))
        self.output_fp.flush()


    def get_first_toolchange(self):
        for line in self.gcode_fp:
            match = re.match(self.toolchange, line)
            if match is not None:
                initial_tool = int(match.group(1))
                break
        self.gcode_fp.seek(0)
        return initial_tool


    def process_gcode_file(self, gcode_file_path, output_file_path, callback=None):
    #This process gcode from a file, and output to a file

        self.last_tool = -1
        self.last_snort_position = 0
        self.last_squirt_position = 0
        self.code_index = 0
        self.gcode_fp = open(gcode_file_path, 'r')
        self.output_fp = open(output_file_path, 'w+')

        #self.write_preprint_purge(True)
        
        #snort the inactive tool at the start of the print
        #self.snort_inactive_tool(True)

        initial_tool = self.get_first_toolchange()

        toolchange = False
        #while copying the file look for the first significant toolchange
        #and reverse the retract
        for line in self.gcode_fp:
            if(not toolchange):
                match = re.match(self.toolchange, line)
                if match is not None:
                    if(int(match.group(1)) != initial_tool):
                        self.output_fp.write(line)
                        self.squirt_inactive_tool(match.group(1), 0, True, doToolchange=False)
                        #This is where further processing will start from
                        toolchange = True
                        continue
            self.output_fp.write(line)
            self.output_fp.flush()
        self.gcode_fp.close()

        self.gcodes = self.index_file(output_file_path, 0)
        self.max_index = (len(self.gcodes)-1)

        while(True):
            self.output_fp.seek(self.gcodes[self.code_index])
            current_code = self.output_fp.readline()

            self.match = re.match(self.toolchange, current_code)
            if self.match is not None:
                if(self.last_tool == -1):
                    self.last_tool = self.match.group(1)
                elif(self.last_tool != self.match.group(1)):
                #If this is a significant tool change
                    self.last_tool = self.match.group(1)

                    #search for the next squirt
                    squirt_index,extruder,current_feedrate,current_position,current_line_len = self.squirt_search(is_GcodeFile=True)
                    #If a squirt was found handle the modification of the squirt
                    if(squirt_index != None):
                        squirt_feedrate = self.squirt_feedrate
                        squirt_position = current_position - self.squirt_reduction
                        self.last_squirt_position = squirt_position
                        
                        if(squirt_position < 0):
                            squirt_position = 0
                        if(self.slicer == 'miracle_grue' or self.slicer == 'skeinforge'):
                            formatted_squirt = self.format_squirt(
                                squirt_feedrate, squirt_position, extruder, current_line_len, squirt_index)             
                            self.insert_snortsquirt(formatted_squirt, squirt_index)

                    #search backwards for the last snort
                    snort_index,extruder,current_feedrate,current_position,current_line_len = self.reverse_snort_search(is_GcodeFile=True)
                    #if a snort was not found in the previous slice continue on
                    if((current_feedrate == None) or (current_position == None)):
                        self.code_index += 1
                        continue
                    #Handling Snort Modification
                    #emit a new snort with a new feedrate and extruder position
                    snort_feedrate = self.snort_feedrate
                    snort_extruder_pos = current_position-self.retract_distance_mm
                    self.last_snort_position = snort_extruder_pos

                    #if(snort_extruder_pos < 0):
                    #    snort_extruder_pos = 0
                    if(self.slicer == 'miracle_grue' or self.slicer == 'skeinforge'):
                        formatted_snort = self.format_snort(
                            snort_feedrate, snort_extruder_pos, extruder, current_line_len, snort_index)
                        self.insert_snortsquirt(formatted_snort, snort_index)

            if(self.code_index < self.max_index):
                self.code_index += 1
            else:
                break

        #post print squirt the inactive tool
        if(int(self.last_tool) == 0):
            tool = 1
        else:
            tool = 0

        self.output_fp.seek(0,2)

        self.squirt_inactive_tool(tool, 0, True, doToolchange=True)
        self.output_fp.close()
        return True


    def squirt_search(self, is_GcodeFile):
        squirt_index = self.code_index+1
        feedrate = None
        position = None

        while(True):
            if(is_GcodeFile):
                self.output_fp.seek(self.gcodes[squirt_index])
                current_code = self.output_fp.readline()
            else:
                current_code = self.gcodes[squirt_index]
            squirt_match = re.match(self.MG_squirt, current_code)
            if squirt_match is not None:
                self.slicer = 'miracle_grue'
                feedrate = float(squirt_match.group(1))
                extruder = squirt_match.group(2)
                position = float(squirt_match.group(3))
                break
            squirt_match = re.match(self.SF_snortsquirt, current_code)
            if squirt_match is not None:
                self.slicer = 'skeinforge'
                position = float(squirt_match.group(1))
                self.output_fp.seek(self.gcodes[squirt_index-1])
                current_code = self.output_fp.readline()
                match = re.match(self.SF_feedrate, current_code)
                if match is not None:
                    feedrate = float(match.group(1)) 
                else:
                    return(None,None,None,None,None)  
                feedrate = float(current_code.split('F')[1])
                extruder = None
                break

            squirt_index += 1
            if(self.slicer == 'miracle_grue'):
                #if a new layer is encountered return
                squirt_match = re.match(self.layer_start, current_code)
                if((squirt_index > self.max_index) or (squirt_match is not None)):
                    return None, None, None, None, None
            if(self.slicer == 'skeinforge'):
                squirt_match = re.match(self.SF_layer_end, current_code)
                if((squirt_index > self.max_index) or (squirt_match is not None)):
                    return None, None, None, None, None

        #if the current extruder position is equal to the last extruder position
        #assume it was modified already and return
        if(position == self.last_squirt_position):
            return(None,None,None,None,None)
        else:
            self.last_squirt_position = position

        return (squirt_index, extruder, feedrate, position, len(squirt_match.group()))


    def format_squirt(self, squirt_feedrate, squirt_position, extruder, current_line_len, line_index):

        if(line_index != None):
            if(self.slicer == 'miracle_grue'):
                new_squirt = "G1 F%.3f %s%.3f (squirt)\n"%(squirt_feedrate,extruder,squirt_position)
                if(len(new_squirt) < current_line_len):
                    formatted_squirt = self.pad_line(new_squirt, current_line_len)
                else:
                    formatted_squirt = new_squirt
                return formatted_squirt

            elif(self.slicer == 'skeinforge'):
                self.output_fp.seek(self.gcodes[line_index-1])
                feedrate_line_len = len(self.output_fp.readline())
                total_len = current_line_len + feedrate_line_len
                new_squirt = "G1 F%.1f\nG1 E%.2f\n"%(squirt_feedrate, squirt_position)
                formatted_squirt = self.pad_line(new_squirt, total_len)
                while(formatted_squirt[-1] == '\n'):
                    formatted_squirt = formatted_squirt[:-1]
                return formatted_squirt + '\n'


    def reverse_snort_search(self, is_GcodeFile):
        snort_index = self.code_index-2
        feedrate = None
        position = None
        layer_starts = 0

        while(True):
            if(is_GcodeFile):
                self.output_fp.seek(self.gcodes[snort_index])
                current_code = self.output_fp.readline()
            else:
                current_code = self.gcodes[snort_index]
            snort_match = re.match(self.MG_snort, current_code)
            if snort_match is not None:
                self.slicer = 'miracle_grue'
                feedrate = float(snort_match.group(1))
                extruder = snort_match.group(2)
                position = float(snort_match.group(3))
                break
            snort_match = re.match(self.SF_snortsquirt, current_code)
            if snort_match is not None:
                self.slicer = 'skeinforge'
                self.output_fp.seek(self.gcodes[snort_index-1])
                current_code = self.output_fp.readline()
                match = re.match(self.SF_feedrate, current_code)
                if match is not None:
                    feedrate = float(match.group(1)) 
                else:
                    return(None,None,None,None,None)   
                position = float(snort_match.group(1))
                extruder = None
                break

            snort_index -= 1


            #if a new layer was encountered and another layer was parsed, return
            snort_match = re.match(self.layer_start, current_code)
            if(snort_match is not None):
                if((snort_index < 0) or (layer_starts > 0)):
                    return(None, None, None, None, None)
                layer_starts += 1

        #if this snort was encountered before, return
        if(position == self.last_snort_position):
            return(None,None,None,None,None)
        else:
            self.last_snort_position = position

        return (snort_index, extruder, feedrate, position, len(snort_match.group()))
            

    def format_snort(self, new_feedrate, new_extruder_pos, extruder, old_line_len, line_index):
        formatted_move_line = None
        if(self.slicer == 'miracle_grue'):
            self.output_fp.seek(self.gcodes[line_index])
            new_move_line = "G1 F%.3f %s%.3f (snort)\n"%(new_feedrate,extruder,new_extruder_pos)
            formatted_move_line = self.pad_line(new_move_line, old_line_len)
            while(formatted_move_line[-1] == '\n'):
                formatted_move_line = formatted_move_line[:-1]

        elif(self.slicer == 'skeinforge'):
            self.output_fp.seek(self.gcodes[line_index-1])
            feedrate_line_len = len(self.output_fp.readline())
            total_len = old_line_len + feedrate_line_len
            new_move_line = "G1 F%.1f\nG1 E%.2f\n"%(new_feedrate, new_extruder_pos)
            formatted_move_line = self.pad_line(new_move_line, total_len)
            while(formatted_move_line[-1] == '\n'):
                formatted_move_line = formatted_move_line[:-1]
        return (formatted_move_line+'\n')


    def insert_snortsquirt(self, snortsquirt_line, snortsquirt_index):
        if(self.slicer == 'miracle_grue'):            
            self.output_fp.seek(self.gcodes[snortsquirt_index])
            self.output_fp.write(snortsquirt_line)
        if(self.slicer == 'skeinforge'):
            self.output_fp.seek(self.gcodes[snortsquirt_index-1])
            #seek to index-1 because SF puts feedrate and extruder position on two lines
            self.output_fp.write(snortsquirt_line)


    def pad_line(self, line, old_line_len):
        if(len(line) < old_line_len):
            line = line[:-1]
            line += (' '*(old_line_len - len(line)))
        return line
        

    def index_file(self, filename, start_index):
        line_indexes = []
        
        with open(filename, 'r') as f:
            f.seek(start_index)
            while(True):
               line_indexes.append(f.tell())
               line = f.readline()
               if(line == ''):
                    break
            return line_indexes

                