import numpy as np
import gui2
import time

class ExtrusionCalculator:
    def __init__(self, syringe_diameter_mm, needle_diameter_mm, hole_diameter_mm, hole_depth_mm, retract_dist_mm):
        self.syringe_id_mm = syringe_diameter_mm
        self.needle_id_mm = needle_diameter_mm
        self.hole_id_mm = hole_diameter_mm
        self.hole_depth_mm = hole_depth_mm
        self.count = 0
        self.retract_dist_mm = retract_dist_mm

    def calculate_extrusion_length(self):
        syringe_radius_mm = self.syringe_id_mm / 2
        needle_radius_mm = self.needle_id_mm / 2
        hole_radius_mm = self.hole_id_mm / 2

        syringe_area_mm2 = np.pi * (syringe_radius_mm ** 2)
        needle_area_mm2 = np.pi * (needle_radius_mm ** 2)
        hole_area_mm2 = np.pi * (hole_radius_mm ** 2)

        volume_hole_mm3 = hole_area_mm2 * self.hole_depth_mm

        extrusion_length_mm = volume_hole_mm3 / syringe_area_mm2

        return extrusion_length_mm
    
    def extrude_hole(self):
        # Placeholder for extrusion command
        length = self.calculate_extrusion_length()
        print(f"Extruding {length:.2f} mm of material.")
        gui2.send_gcode(f"G1 Z-1.5 F100")
        gui2.send_gcode(f"G91")  # Relative positioning
        gui2.send_gcode(f"G1 B{self.count*self.retract_dist_mm + length} F100")
        time.sleep(2)
        gui2.send_gcode(f"G90")  # Absolute positioning
        self.count += 1

    def retract(self):
        gui2.send_gcode(f"G91")  # Relative positioning
        gui2.send_gcode(f"G1 B-{self.retract_dist_mm} F100")
        time.sleep(1)
        gui2.send_gcode(f"G90")  # Absolute positioning
