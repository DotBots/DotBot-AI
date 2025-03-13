import sensor, image, time, os, ml, math, uos, gc
from ulab import numpy as np
from machine import LED, I2C, UART
from vl53l1x import VL53L1X

# Configuración UART
uart = UART("LP1", 115200)

# Time of flight sensor
tof = VL53L1X(I2C(2))

# Configuración de la cámara
sensor.reset()                         # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565)    # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)      # Set frame size to QVGA (320x240)
sensor.set_windowing((240, 240))       # Set 240x240 window.
sensor.skip_frames(time=2000)          # Let the camera adjust.

# Cargar el modelo y las etiquetas
net = None
labels = None
min_confidence = 0.7
led = LED("LED_RED")

try:
    net = ml.Model("trained_stitch.tflite", load_to_fb=uos.stat('trained_stitch.tflite')[6] > (gc.mem_free() - (64*1024)))
except Exception as e:
    raise Exception('Failed to load "trained.tflite" (' + str(e) + ')')

try:
    labels = [line.rstrip('\n') for line in open("labels_stitch.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt" (' + str(e) + ')')

colors = [ # Add more colors if you are detecting more than 7 types of classes at once.
    (255,   0,   0),
    (  0, 255,   0),
    (255, 255,   0),
    (  0,   0, 255),
    (255,   0, 255),
    (  0, 255, 255),
    (255, 255, 255),
]

threshold_list = [(math.ceil(min_confidence * 255), 255)]

def fomo_post_process(model, inputs, outputs):
    ob, oh, ow, oc = model.output_shape[0]

    x_scale = inputs[0].roi[2] / ow
    y_scale = inputs[0].roi[3] / oh

    scale = min(x_scale, y_scale)

    x_offset = ((inputs[0].roi[2] - (ow * scale)) / 2) + inputs[0].roi[0]
    y_offset = ((inputs[0].roi[3] - (ow * scale)) / 2) + inputs[0].roi[1]

    l = [[] for i in range(oc)]

    for i in range(oc):
        img = image.Image(outputs[0][0, :, :, i] * 255)
        blobs = img.find_blobs(
            threshold_list, x_stride=1, y_stride=1, area_threshold=1, pixels_threshold=1
        )
        for b in blobs:
            rect = b.rect()
            x, y, w, h = rect
            score = (
                img.get_statistics(thresholds=threshold_list, roi=rect).l_mean() / 255.0
            )
            x = int((x * scale) + x_offset)
            y = int((y * scale) + y_offset)
            w = int(w * scale)
            h = int(h * scale)
            l[i].append((x, y, w, h, score))
    return l

proximity_threshold = 200  

clock = time.clock()

def group_centroids(detections, distance_threshold=200):
    """
    Groups nearby centroids and returns a filtered list of detections.
    - distance_threshold: Maximum distance between centroids to consider them the same object.
    """
    if not detections:
        return []

    filtered_detections = []
    used = set()

    for i, (x1, y1, w1, h1, score1) in enumerate(detections):
        if i in used:
            continue
        group = [(x1, y1, score1)]
        used.add(i)

        for j, (x2, y2, w2, h2, score2) in enumerate(detections):
            if j in used:
                continue
            if math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) < distance_threshold:
                group.append((x2, y2, score2))
                used.add(j)

        # Choose the centroid with the highest score or calculate average
        best_x = int(sum(g[0] * g[2] for g in group) / sum(g[2] for g in group))
        best_y = int(sum(g[1] * g[2] for g in group) / sum(g[2] for g in group))

        filtered_detections.append((best_x, best_y))

    return filtered_detections

while True:
    clock.tick()
    img = sensor.snapshot()
    distance = tof.read()

    detections = []
    for i, detection_list in enumerate(net.predict([img], callback=fomo_post_process)):
        if i == 0: 
            continue  
        for x, y, w, h, score in detection_list:
            center_x = x + w // 2
            center_y = y + h // 2
            detections.append((center_x, center_y, w, h, score))

    # Filter centroids by grouping the nearby ones
    filtered_detections = group_centroids(detections)

    if not filtered_detections:
        data = bytearray([255, 0, 0])
        uart.write(data)
	led.off()
        time.sleep_ms(5)
    else:
        for center_x, center_y in filtered_detections:            
            img.draw_circle((center_x, center_y, 12), color=colors[i])
            led.on()
            data = [255, 1, center_y]
            uart.write(bytearray(data))
            time.sleep_ms(5)
            #print(f"Data sent: {list(data)}")

    #if distance<proximity_threshold:
    #    print("Object too close! Stop!")

    #print(f"Proximity: {distance}mm")
    #print(clock.fps(), "fps", end="\n\n")