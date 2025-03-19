import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640,480)}))
picam2.start()

fps = 30
frame_width = 640
frame_height = 480

lower_red = np.array([0,120,70])
upper_red = np.array([10, 255, 255])

lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])

lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])

gst_str_rtp = "appsrc ! videoconvert ! video/x-raw,format=BGR ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=172.20.10.2 port=5000"

out = cv2.VideoWriter(f"gst-launch-1.0 {gst_str_rtp}", cv2.CAP_GSTREAMER, 0, fps, (frame_width, frame_height), True)


position = 0.0

while True:
    im = picam2.capture_array()

    hsv_frame = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

    mask_red = cv2.inRange(hsv_frame, lower_red, upper_red)
    mask_yellow = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)
    mask_blue = cv2.inRange(hsv_frame, lower_blue, upper_blue)

    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def process_contours(contours, color, label, frame):
        for contour in contours:
            # Calculate contour area and perimeter
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)

            if perimeter > 0:  # Avoid division by zero
                circularity = 4 * np.pi * (area / (perimeter ** 2))
                if 0.7 < circularity <= 1.2:  # Filter by circularity
                    # Get the minimum enclosing circle
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    center = (int(x), int(y))
                    radius = int(radius)

                    if radius > 10:  # Ignore very small circles
                        # Draw the circle and label it
                        cv2.circle(frame, center, radius, color, 2)
                        cv2.putText(frame, label, (int(x - radius), int(y - radius - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    process_contours(contours_red, (0,0,255), "RED", im)
    process_contours(contours_yellow, (0,255,255), "YELLOW", im)
    process_contours(contours_blue, (255, 0, 0), "BLUE", im)
    im = im.astype(np.uint8)
    out.write(im)
    cv2.imshow("Camera", im)
    key = cv2.waitKey(1)
    # picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": position})
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    if key & 0xFF == ord('q'):
        exit()
    if key & 0xFF == ord('i'):
        position+=0.1
    if key & 0xFF == ord('d'):
        position-=0.1
    if key & 0xFF == ord('p'):
        picam2.start_and_capture_file("test.png")






