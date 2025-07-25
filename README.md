## EXTRUSION TARGETTING SOFTWARE ##

(1) Take Snapshot -> Snapshot of current frame of live feed is taken and written to "frames"
(2) Calibrate -> API call sends snapshot to custom trained YOLOv8 compatible model hosted on roboflow, receives response, and plots center points on live feed 
(3) Run Conversion -> OpenCV script determines pixel/mm ratio and returns in console
(4) Home (Top Right) -> Printer homes to top right electrode using sendToPrinter() utility function through port selected 