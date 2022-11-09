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

ALL_FILES = ["vulkan_core.h"] + FILES


def get_funcs_from_pickle(pfile):
    with open(pfile, "rb") as f:
        rs = pickle.load(f)
    res = []
    for (feature, funcs) in rs:
        res += funcs
    return res


def get_all_funcs():
    res = []
    for header in ALL_FILES:
        pickle_filename = os.path.join(INPUT_DIR, header + ".pkl")
        funcs = get_funcs_from_pickle(pickle_filename)
        res.append([header, funcs])

    return res


def check_funcs(funcs):
    for func in funcs:
        n = len(func[2])
        assert n == len(func[3])
        assert n == len(func[4])

# 0 return_type
# 1 func_name
# 2 param_item_lst
# 3 param_type_lst
# 4 param_name_lst
# 5 first_param_type

def get_inst_funcs(all_funcs):
    res = []
    for (header, funcs) in all_funcs:
        new_funcs = [func for func in funcs if func[5] in ("VkInstance", "VkPhysicalDevice") and func[1] not in ("vkGetInstanceProcAddr",) ]
        check_funcs(new_funcs)
        res.append([header, new_funcs])

    return res


def get_dev_funcs(all_funcs):
    res = []
    for (header, funcs) in all_funcs:
        new_funcs = [func for func in funcs if func[5] in ("VkDevice", "VkCommandBuffer", "VkQueue") ]
        check_funcs(new_funcs)
        res.append([header, new_funcs])

    return res


def get_lib_funcs(all_funcs):
    res = []
    for (header, funcs) in all_funcs:
        new_funcs = [func for func in funcs if func[5] not in ("VkInstance", "VkPhysicalDevice", "VkDevice", "VkCommandBuffer", "VkQueue") or func[1] in ("vkGetInstanceProcAddr", ) ]
        check_funcs(new_funcs)
        res.append([header, new_funcs])

    func1 = ["VkBool32", "vkDebugUtilsMessengerCallbackEXT",
                ["VkDebugUtilsMessageSeverityFlagBitsEXT messageSeverity",
                 "VkDebugUtilsMessageTypeFlagsEXT messageTypes",
                 "const VkDebugUtilsMessengerCallbackDataEXT * pCallbackData",
                 "void * pUserData"],
                ["VkDebugUtilsMessageSeverityFlagBitsEXT ",
                 "VkDebugUtilsMessageTypeFlagsEXT ",
                 "const VkDebugUtilsMessengerCallbackDataEXT * ",
                 "void * "],
                ["messageSeverity",
                 "messageTypes",
                 "pCallbackData",
                 "pUserData"],
                 "VkDebugUtilsMessageSeverityFlagBitsEXT"
            ]

    func2 = ["VkBool32", "vkDebugReportCallbackEXT",
                ["VkDebugReportFlagsEXT flags",
                 "VkDebugReportObjectTypeEXT objectType",
                 "uint64_t object",
                 "size_t location",
                 "int32_t messageCode",
                 "const char * pLayerPrefix",
                 "const char * pMessage",
                 "void * pUserData"],
                ["VkDebugReportFlagsEXT ",
                 "VkDebugReportObjectTypeEXT ",
                 "uint64_t ",
                 "size_t ",
                 "int32_t ",
                 "const char * ",
                 "const char * ",
                 "void * "],
                ["flags",
                 "objectType",
                 "object",
                 "location",
                 "messageCode",
                 "pLayerPrefix",
                 "pMessage",
                 "pUserData"],
                "VkDebugReportFlagsEXT"
            ]

    check_funcs([func1, func2])
    res.append(["other.h", [func1, func2]])

    return res


def ret_val(ret_type):
    if ret_type.startswith("PFN_"):
        return "null"
    if ret_type == "VkResult":
        return "VK_RESULT_MAX_ENUM"
    assert ret_type == "VkBool32"
    return "VkBool32(0)"


def platform_guard(header):
    return header in [
         # 'vulkan_core.h',
         'vulkan_win32.h',
         'vulkan_android.h',
         'vulkan_xlib.h',
         'vulkan_xlib_xrandr.h',
         'vulkan_xcb.h',
         'vulkan_wayland.h',
     ]


def platform_guard_macro(header):
    return header.replace(".h", "_H_").upper()


def write_header_section(f, sec_funcs, macro, write_func):
    f.write("#ifdef {MACRO}\n".format(MACRO=macro))

    for (header, funcs) in sec_funcs:
        if len(funcs) > 0:
            if platform_guard(header):
                f.write("# ifdef {MACRO}\n".format(MACRO=platform_guard_macro(header)))

            for func in funcs:
                write_func(f, func)

            if platform_guard(header):
                f.write("# endif // {MACRO}\n".format(MACRO=platform_guard_macro(header)))

    f.write("#endif // {MACRO}\n\n\n".format(MACRO=macro))


def write_func_decl_fn_pointer(f, func):
    f.write("    extern PFN_{FUNC_NAME}  _var_{FUNC_NAME};\n".format(FUNC_NAME=func[1]))


def write_func_fn_pointer(f, func):
    f.write("    PFN_{FUNC_NAME}  _var_{FUNC_NAME} = null;\n".format(FUNC_NAME=func[1]))
def gen_lib_header(lib_funcs):
    header_file = os.path.join(OUTPUT_DIR, "fn_vulkan_lib2.h")

    with open(header_file, "w") as f:
        write_header_section(f, lib_funcs, "VKLOADER_STAGE_DECLFNPOINTER", write_func_decl_fn_pointer)
        write_header_section(f, lib_funcs, "VKLOADER_STAGE_FNPOINTER", write_func_fn_pointer)

        f.write("#ifdef VKLOADER_STAGE_INLINEFN\n")
        for (header, funcs) in lib_funcs:
            for func in funcs:
                f.write("    ND_ VKAPI_ATTR forceinline VkResult {FUNC_NAME} ({PARAM_ITEMS})".format(FUNC_NAME=func[1], PARAM_ITEMS=(', '.join(func[2]))))
                f.write(" {{ return _var_{FUNC_NAME}( {PARAM_NAMES} ); }}\n".format(FUNC_NAME=func[1], PARAM_NAMES=(', '.join(func[4]))))
        f.write("#endif // VKLOADER_STAGE_INLINEFN\n\n\n")

        f.write("#ifdef VKLOADER_STAGE_DUMMYFN\n")
        for (header, funcs) in lib_funcs:
            for func in funcs:
                f.write("    VKAPI_ATTR {RETURN_TYPE} VKAPI_CALL Dummy_{FUNC_NAME} ({PARAM_TYPES})".format(RETURN_TYPE=func[0], FUNC_NAME=func[1], PARAM_TYPES=(', '.join(func[3]))))
                f.write(" {{  FG_LOGI( \"used dummy function '{FUNC_NAME}'\" );  return {RETURN_VALUE};  }}\n".format(FUNC_NAME=func[1], RETURN_VALUE=ret_val(func[0])))
        f.write("#endif // VKLOADER_STAGE_DUMMYFN\n\n\n")

        f.write("#ifdef VKLOADER_STAGE_GETADDRESS\n")
        for (header, funcs) in lib_funcs:
            for func in funcs:
                f.write("    Load( OUT _var_{FUNC_NAME}, \"{FUNC_NAME}\", Dummy_{FUNC_NAME} );\n".format(FUNC_NAME=func[1]))
        f.write("#endif // VKLOADER_STAGE_GETADDRESS\n\n\n")


if __name__ == '__main__':
    all_funcs = get_all_funcs()

    inst_funcs = get_inst_funcs(all_funcs)
    print(inst_funcs)
    for (header, funcs) in inst_funcs:
        print(header, len(funcs))

    dev_funcs = get_dev_funcs(all_funcs)
    print(dev_funcs)
    for (header, funcs) in dev_funcs:
        print(header, len(funcs))

    lib_funcs = get_lib_funcs(all_funcs)
    print(lib_funcs)
    for (header, funcs) in lib_funcs:
        print(header, len(funcs))
    gen_lib_header(lib_funcs)

