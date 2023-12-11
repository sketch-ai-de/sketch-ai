from enum import Enum


class DeviceType(Enum):
    MOTOR = 1
    MOTOR_DRIVE = 2
    PLC_CPU = 3
    PLC_IO_MODULE_SYSTEM = 4
    PLC_IO_MODULE = 5
    ROBOT_ARM = 6
    MICROCONTROLLER_BOARD = 7
    INDUCTIVE_SENSOR = 8
    COMPUTER = 9
    ROBOT_SERVO_DRIVE_JOINT = 10


device_type_list = [el.name for el in DeviceType]
device_type_dict = {el.name: el.value for el in DeviceType}


class DocumentTypeRobotArm(Enum):
    HARDWARE = 1
    SOFTWARE = 2
    CONTROL_BOX = 3
    GRIPPER = 4


document_type_robot_arm_list = [el.name for el in DocumentTypeRobotArm]
document_type_robot_arm_dict = {el.name: el.value for el in DocumentTypeRobotArm}
