import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()
picam2.configuration(picam2.create_preview_configuration(main={"format":'XRGB8888', "size":(640,480)}))
picam2.start()

fps = 30
frame_width = 640
frame_height = 480

position = 0.0

# Camera setup
cap = cv2.VideoCapture(0)  # Change to your camera index if needed
#delete above put the rasberry pie camera settings above

# Define color ranges in HSV
color_ranges = {
    "RED": [(np.array([0, 150, 70]), np.array([10, 255, 255])),  # Focus on bright red
            (np.array([170, 150, 70]), np.array([180, 255, 255]))],  # Focus on dark red
    "YELLOW": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
    "BLUE": [(np.array([100, 150, 0]), np.array([140, 255, 255]))]
}


def process_contours(contours, frame, color_name):
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)  # Find the largest contour
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        if perimeter == 0:
            return
        circularity = 4 * np.pi * (area / (perimeter ** 2))

        (x, y), radius = cv2.minEnclosingCircle(largest_contour)
        center = (int(x), int(y))
        radius = int(radius)

        if radius > 10:  # Accept only significant objects
            cv2.circle(frame, center, radius, (0, 255, 0), 3)
            label = f"{color_name} Object"

            # Categorize the object based on circularity
            if circularity > 0.7:
                label += " - Possible Target"
            else:
                label += " - Not Target"

            cv2.putText(frame, label, (center[0] - 40, center[1] - radius - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


while cap.isOpened():
    im = picam2.capture_array()

    hsv_frame = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

    for color, ranges in color_ranges.items():
        mask = sum([cv2.inRange(hsv_frame, lower, upper) for lower, upper in ranges])
        mask = cv2.medianBlur(mask, 5)  # Reduce noise
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        process_contours(contours, im, color)

    cv2.imshow("Drone Camera Feed", im)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
