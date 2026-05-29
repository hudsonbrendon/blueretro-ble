"""BlueRetro BLE protocol constants (from darthcloud/BlueRetroWebCfg)."""

SERVICE_UUID = "56830f56-5180-fab0-314b-2fa176799a00"

# Directly readable/writable characteristics
CHAR_GLOBAL_CFG = "56830f56-5180-fab0-314b-2fa176799a01"
CHAR_OUTPUT_CTRL = "56830f56-5180-fab0-314b-2fa176799a02"  # write uint16 output index
CHAR_OUTPUT_DATA = "56830f56-5180-fab0-314b-2fa176799a03"  # [device, accessory] bytes
CHAR_IN_CFG_CTRL = "56830f56-5180-fab0-314b-2fa176799a04"  # write uint16[2]=[cfg_id, offset]
CHAR_IN_CFG_DATA = "56830f56-5180-fab0-314b-2fa176799a05"  # input mapping blob (512-chunked)
CHAR_ABI = "56830f56-5180-fab0-314b-2fa176799a06"
CHAR_CMD = "56830f56-5180-fab0-314b-2fa176799a07"
CHAR_OTA_FW_DATA = "56830f56-5180-fab0-314b-2fa176799a08"  # OTA firmware data (MTU chunks)
CHAR_APP = "56830f56-5180-fab0-314b-2fa176799a09"
CHAR_FILE_CTRL = "56830f56-5180-fab0-314b-2fa176799a0a"  # write uint32 offset (reset 0)
CHAR_FILE_DATA = "56830f56-5180-fab0-314b-2fa176799a0b"  # chunked file data (VMU/pak)
CHAR_BDADDR = "56830f56-5180-fab0-314b-2fa176799a0c"

# Command bytes written to CHAR_CMD, response read back from CHAR_CMD
CMD_GET_GAMEID = 0x04
CMD_GET_CFG_SRC = 0x05
CMD_GET_FILE = 0x06
CMD_GET_FW_NAME = 0x07
CMD_OPEN_DIR = 0x12
CMD_CLOSE_DIR = 0x13
CMD_DEL_FILE = 0x14
CMD_SYS_DEEP_SLEEP = 0x37
CMD_SYS_RESET = 0x38
CMD_SYS_FACTORY = 0x39
CMD_OTA_END = 0x5A
CMD_OTA_START = 0xA5
CMD_OTA_ABORT = 0xDE

# Advertised BLE name prefix used for discovery
NAME_PREFIX = "BlueRetro"

# Global config byte enums (index -> label), from BlueRetroWebCfg utils/constants.js.
# The global config characteristic (CHAR_GLOBAL_CFG) carries one byte per field:
#   byte 0 = system, byte 1 = multitap, byte 2 = inquiry mode, byte 3 = card bank.
SYSTEM_CFG = (
    "Auto",
    "Parallel_1P_PP",
    "Parallel_2P_PP",
    "NES",
    "PCE",
    "MD-Genesis",
    "SNES",
    "CD-i",
    "CD32",
    "3DO",
    "Jaguar",
    "PSX",
    "Saturn",
    "PC-FX",
    "JVS",
    "N64",
    "DC",
    "PS2",
    "GC",
    "Wii-Ext",
    "VB",
    "Parallel_1P_OD",
    "Parallel_2P_OD",
    "SEA Board",
)
MULTITAP_CFG = ("None", "Slot 1", "Slot 2", "Dual", "Alt")
INQUIRY_MODE = ("Auto", "Manual")

# Per-output config (CHAR_OUTPUT_DATA): byte 0 = device mode, byte 1 = accessory.
DEVICE_CFG = ("GamePad", "GamePadAlt", "Keyboard", "Mouse")
ACCESSORY_CFG = ("None", "Memory", "Rumble", "Both")
MAX_OUTPUT = 12

# Dreamcast VMU (visual memory unit) image size, transferred in chunks over
# CHAR_FILE_CTRL (offset) + CHAR_FILE_DATA.
VMU_SIZE = 128 * 1024
FILE_CHUNK = 244  # MTU-sized write chunk
MC_BLOCK = 4096  # memory-card flash block; file writes never cross this boundary

# N64 Controller Pak: 4 banks of 32 KiB in the same flat memory-card buffer.
PAK_SIZE = 32 * 1024
PAK_BANKS = 4

# Input mapping config (CHAR_IN_CFG_CTRL/DATA): blob is [0, 0, n_mappings] then
# n_mappings * 8-byte entries; transferred in 512-byte chunks.
IN_CFG_CHUNK = 512
MAX_MAPPINGS = 255
