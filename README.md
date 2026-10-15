# Smart Room Assistant Robot (ROS 2)

A voice-controlled indoor mobile robot simulation built with **ROS 2 Jazzy, Gazebo, TurtleBot3, Nav2, OpenCV and YOLO11**.
Say a room name, and the robot navigates there, scans the room in 360°, and reports which objects it finds.

## Features

* Voice-based room selection (Google Speech Recognition)
* Autonomous navigation with Nav2 on a saved map
* 360-degree room scan
* Object detection with a **fine-tuned YOLO11 model** (coke can, red ball, yellow box): mAP50 0.94, recall 1.00 on the validation set
* Baseline colour detection with OpenCV (HSV thresholding)
* Custom Gazebo house world with objects placed in the rooms

## How it works

1. Voice command ("go to kitchen")
2. SpeechRecognition converts speech to text
3. Room name is matched to predefined X/Y coordinates
4. A NavigateToPose goal is sent to Nav2
5. The robot rotates 360 degrees while processing `/camera/image_raw`
6. YOLO11 detects objects in each frame and the scan reports every object found with its confidence

## Object detection: from HSV to YOLO

The first version used HSV colour thresholding to find blue objects. A pretrained YOLO model performed poorly on the simulated objects, so I trained my own:

1. Placed objects in the Gazebo house world
2. Collected ~285 images from the robot camera while driving through the house (`object_detection/capture_images.py`)
3. Labelled them in Roboflow (3 classes: `coke`, `red ball`, `yellow box`)
4. Fine-tuned **YOLO11n** on Google Colab (T4 GPU, 60 epochs, 640×640)
5. Integrated the model into a 360° room scan (`object_detection/yolo_room_scan.py`)

| Metric (validation set) | Value |
|---|---|
| mAP50 | 0.94 |
| mAP50-95 | 0.88 |
| Precision | 0.87 |
| Recall | 1.00 |

In repeated room scans, the robot detected all three objects with confidence between 0.67 and 0.94.

## Repository structure

* `voice_navigation/`: voice commands and room navigation goals
* `object_detection/`: room scans (HSV and YOLO), image capture for training, trained weights (`best.pt`)
* `launch/`: launch file for the custom house world
* `worlds/`: Gazebo house world with objects
* `maps/`: saved map (.yaml and .pgm)
* `experiments/`: early YOLO tests with a pretrained model

## Requirements

* Ubuntu 24.04, ROS 2 Jazzy, Gazebo, Nav2
* TurtleBot3 packages (`burger_cam` model)
* Python 3: opencv-python, numpy<2, SpeechRecognition, PyAudio, ultralytics
* cv_bridge

```bash
pip install ultralytics "numpy<2" SpeechRecognition pyaudio --break-system-packages
```

## Running

1. Launch Gazebo with the house world and the robot:

```bash
export TURTLEBOT3_MODEL=burger_cam
ros2 launch launch/house_project.launch.py
```

2. Start Nav2 with the saved map, then set the initial pose with **2D Pose Estimate** in RViz:

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=maps/new_house_map_final.yaml
```

3. Run voice navigation:

```bash
python3 voice_navigation/voice_room_navigator.py
```

4. Run the YOLO room scan once the robot has reached a room:

```bash
python3 object_detection/yolo_room_scan.py
```

(The HSV baseline is still available: `python3 object_detection/room_scan.py`)

### Collecting new training images

```bash
python3 object_detection/capture_images.py
ros2 run turtlebot3_teleop teleop_keyboard
```

Images are saved to `~/yolo_dataset/raw_images` once per second.

## Limitations

* The detection model is trained on simulated images only, with a small validation set (54 objects)
* Room coordinates are predefined
* Simulation only

## Future work

* Train on more varied data and real camera images
* Object localization on the map (3D position of detected objects)
* Object manipulation with a robot arm
* Physical robot deployment
