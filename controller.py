"""
This script is called by the controller.service
"""
import json
import socket
import os
import RPi.GPIO as GPIO
import pigpio

socket_path = '/tmp/uv4l.socket'

try:
    os.unlink(socket_path)
except OSError:
    if os.path.exists(socket_path):
        raise

s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)


# print'socket_path: %s' % socket_path
s.bind(socket_path)
s.listen(1)


def cleanup():
    pass


class Wheels(object):

    def __init__(
            self, r_wheel_forward=6, r_wheel_backward=13, l_wheel_forward=19, l_wheel_backward=26):
        self.r_wheel_forward = r_wheel_forward
        self.r_wheel_backward = r_wheel_backward
        self.l_wheel_forward = l_wheel_forward
        self.l_wheel_backward = l_wheel_backward

        # Setup motors
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(r_wheel_forward, GPIO.OUT)
        GPIO.setup(r_wheel_backward, GPIO.OUT)
        GPIO.setup(l_wheel_forward, GPIO.OUT)
        GPIO.setup(l_wheel_backward, GPIO.OUT)

        # Turn all motors off
        GPIO.output(r_wheel_forward, GPIO.LOW)
        GPIO.output(r_wheel_backward, GPIO.LOW)
        GPIO.output(l_wheel_forward, GPIO.LOW)
        GPIO.output(l_wheel_backward, GPIO.LOW)

    def _spin_right_wheel_forward(self):
        GPIO.output(self.r_wheel_forward, GPIO.HIGH)
        GPIO.output(self.r_wheel_backward, GPIO.LOW)

    def _spin_right_wheel_backward(self):
        GPIO.output(self.r_wheel_backward, GPIO.HIGH)
        GPIO.output(self.r_wheel_forward, GPIO.LOW)

    def _stop_right_wheel(self):
        GPIO.output(self.r_wheel_backward, GPIO.LOW)
        GPIO.output(self.r_wheel_forward, GPIO.LOW)

    def _spin_left_wheel_forward(self):
        GPIO.output(self.l_wheel_forward, GPIO.HIGH)
        GPIO.output(self.l_wheel_backward, GPIO.LOW)

    def _spin_left_wheel_backward(self):
        GPIO.output(self.l_wheel_backward, GPIO.HIGH)
        GPIO.output(self.l_wheel_forward, GPIO.LOW)

    def _stop_left_wheel(self):
        GPIO.output(self.l_wheel_backward, GPIO.LOW)
        GPIO.output(self.l_wheel_forward, GPIO.LOW)

    def go_fw(self):
        self._spin_left_wheel_forward()
        self._spin_right_wheel_forward()

    def go_fw_left(self):
        self._stop_left_wheel()
        self._spin_right_wheel_forward()

    def go_fw_right(self):
        self._spin_left_wheel_forward()
        self._stop_right_wheel()

    def go_bw(self):
        self._spin_left_wheel_backward()
        self._spin_right_wheel_backward()

    def go_bw_right(self):
        self._spin_left_wheel_backward()
        self._stop_right_wheel()

    def go_bw_left(self):
        self._stop_left_wheel()
        self._spin_right_wheel_backward()

    def stop(self):
        self._stop_left_wheel()
        self._stop_right_wheel()

    def turn_right(self):
        self._spin_left_wheel_forward()
        self._spin_right_wheel_backward()

    def turn_left(self):
        self._spin_left_wheel_backward()
        self._spin_right_wheel_forward()


class Camera:
    CENTER = 40000
    UP_LIMIT = 80000
    DOWN_LIMIT = 30000
    STEP = 5000

    def __init__(self, servo=18, freq=50):
        self.servo = servo
        self.freq = freq
        self.pi = pigpio.pi()

        self.angle = self.CENTER
        self._set_angle()

    def _set_angle(self):
        self.pi.hardware_PWM(self.servo, self.freq, self.angle)

    def up(self):
        if self.angle + self.STEP < self.UP_LIMIT:
            self.angle += self.STEP
            self._set_angle()

    def down(self):
        if self.angle - self.STEP > self.DOWN_LIMIT:
            self.angle -= self.STEP
            self._set_angle()


MAX_MESSAGE_SIZE = 4096

if __name__ == "__main__":
    while True:
        wheels = Wheels()
        camera = Camera()
        print('awaiting connection...')
        connection, client_address = s.accept()
        print('client_address %s' % client_address)
        try:
            print('established connection with', client_address)

            while True:
                message = connection.recv(MAX_MESSAGE_SIZE)
                # print('message: {}'.format(message))
                if not message:
                    break
                data = json.loads(message.decode('utf-8'))

                if 'commands' in data:
                    if 'FORDWARD' in data['commands']:
                        if 'RIGHT' in data['commands']:
                            wheels.go_fw_right()
                        elif 'LEFT' in data['commands']:
                            wheels.go_fw_left()
                        else:
                            wheels.go_fw()
                    elif 'BACKWARD' in data['commands']:
                        if 'RIGHT' in data['commands']:
                            wheels.go_bw_right()
                        elif 'LEFT' in data['commands']:
                            wheels.go_bw_left()
                        else:
                            wheels.go_bw()
                    else:
                        if 'RIGHT' in data['commands']:
                            wheels.turn_right()
                        elif 'LEFT' in data['commands']:
                            wheels.turn_left()
                        else:
                            wheels.stop()

                    if 'UP' in data['commands']:
                        camera.up()
                    elif 'DOWN' in data['commands']:
                        camera.down()

            print('connection closed')

        finally:
            # Clean up the connection
            cleanup()
            connection.close()
