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
    SOFTWARE = 11
    PLC_INDUSTRIAL_PC = 12
    PLC_INTERFACE_MODULE = 13
    PLC_POWER_SUPPLY = 14
    PLC_BASE_UNIT = 15
    PLC_BUS_ADAPTER = 16


device_type_list = [el.name for el in DeviceType]
device_type_dict = {el.name: el.value for el in DeviceType}


class DocumentTypeRobotArm(Enum):
    ROBOT_ARM = 1
    SOFTWARE = 2
    CONTROL_BOX = 3
    GRIPPER = 4
    PLC = 5


document_type_robot_arm_list = [el.name for el in DocumentTypeRobotArm]
document_type_robot_arm_dict = {el.name: el.value for el in DocumentTypeRobotArm}
