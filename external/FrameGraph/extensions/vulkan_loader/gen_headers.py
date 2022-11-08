# coding=utf-8

import os
import pickle

INPUT_DIR = r"C:\chang\study\Vulkan-Docs-1.3.216\gen\include\vulkan"
OUTPUT_DIR = r"C:\chang\study\RDCtoVkCpp\external\FrameGraph\extensions\vulkan_loader"

FILES = [
    "vulkan_win32.h",
    "vulkan_android.h",
    "vulkan_xlib.h",
    "vulkan_xlib_xrandr.h",
    "vulkan_xcb.h",
    "vulkan_wayland.h",
]


def get_funcs_from_pickle(pfile):
    with open(pfile, "rb") as f:
        rs = pickle.load(f)
    res = []
    for (feature, funcs) in rs:
        res += funcs
    return res

if __name__ == '__main__':
    pickle_filename = os.path.join(INPUT_DIR, "vulkan_core.h" + ".pkl")
    funcs = get_funcs_from_pickle(pickle_filename)
    print(funcs)
    print("hello")
