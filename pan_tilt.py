import subprocess
import pdb
import re
import time
import datetime
import os

PAN_MIN = -612000
PAN_MAX = +612000

TILT_MIN = -108000
TILT_MAX = 324000

SEC_PER_DEG = (2 / 90)


def move_camera(pan_deg, tilt_deg):
    '''
    pan_deg ranges from -180 to 180 degrees
    tilt_deg ranges from +90 to -30
    '''

    current_pan, current_tilt = get_pan_tilt()
    print(f'pan: {current_pan} -> {pan_deg}')
    print(f'tilt: {current_tilt} -> {tilt_deg}')

    pan_val = int(pan_deg / 180 * PAN_MAX)
    pan_val = min(PAN_MAX, pan_val)
    pan_val = max(PAN_MIN, pan_val)

    tilt_val = int(tilt_deg / 90 * TILT_MAX)
    tilt_val = min(TILT_MAX, tilt_val)
    tilt_val = max(TILT_MIN, tilt_val)

    pan_delta = abs(pan_deg - current_pan)
    tilt_delta = abs(tilt_deg - current_tilt)

    print(f'pan_delta: {pan_delta}')
    print(f'tilt_delta: {tilt_delta}')

    pan_delay_sec  = pan_delta * SEC_PER_DEG
    tilt_delay_sec = tilt_delta * SEC_PER_DEG

    delay_sec = max(pan_delay_sec, tilt_delay_sec)
    print(f'waiting for {delay_sec}')

    cmd = f'v4l2-ctl -d /dev/video0 --set-ctrl pan_absolute={pan_val},tilt_absolute={tilt_val}'
    subprocess.call(cmd, shell=True)

    time.sleep(delay_sec)


def get_pan_tilt():
    cmd = f'v4l2-ctl -d /dev/video0 --get-ctrl tilt_absolute,pan_absolute'
    output = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        encoding='utf-8'
    ).stdout

    match = re.search(r'tilt_absolute: ([-\d]+)\s+pan_absolute: ([-\d]+)', output)

    assert(match)

    print(match.group(0))

    tilt = int( int(match.group(1)) / TILT_MAX * 90 )
    pan = int( int(match.group(2)) / PAN_MAX * 180 )
    
    print(tilt)
    print(pan)

    return pan, tilt



def set_auto_focus():
    cmd = f'v4l2-ctl -d /dev/video0 --set-ctrl focus_automatic_continuous=1'
    subprocess.run(cmd, shell=True, capture_output=True).stdout
    


def take_picture(prefix=''):
    if os.path.exists('frame.mjpg'):
        os.remove('frame.mjpg')

    if os.path.exists('frame.jpg'):
        os.remove('frame.jpg')
    
    assert(False == os.path.exists('frame.mjpg'))
    assert(False == os.path.exists('frame.jpg'))

    NUM_TRIES = 16
    basename = datetime.datetime.now().strftime(f'{prefix}__%y-%m-%d__%H-%M-%S')

    for k in range(NUM_TRIES):
        try:
            cmd = f'v4l2-ctl -d /dev/video0 --set-fmt-video=width=3840,height=2160,pixelformat=MJPG --stream-mmap --stream-to=frame.mjpg --stream-count=1'
            print('taking picture...')
            subprocess.run(cmd, shell=True, capture_output=True, timeout=1).stdout

            if not os.path.exists('frame.mjpg'):
                print('taking a frame failed...')
                continue

            convert_cmd = f'ffmpeg -y -i frame.mjpg -bsf:v mjpeg2jpeg frame.jpg'
            print('converting picture...')
            subprocess.run(convert_cmd, shell=True, capture_output=True, timeout=2).stdout

            if not os.path.exists('frame.jpg'):
                print('converting failed...')
                continue

            if os.path.getsize('frame.jpg') < 100000:
               print('filesize is too small...')
               continue

            break

        except subprocess.TimeoutExpired as te:
            print('Timeout out occurred...')
            continue


    subprocess.run(f'mv frame.jpg {basename}.jpg', shell=True, capture_output=True).stdout

    subprocess.run(f'rm frame.mjpg', shell=True, capture_output=True).stdout

    print(basename)

    return f'{basename}.jpg'



if __name__ == '__main__':
   print(
      subprocess.run('rm *.jpg', shell=True).stdout
   )

   pan, tilt = get_pan_tilt()


   move_camera(pan_deg=0, tilt_deg=90)
   set_auto_focus()
   take_picture()

