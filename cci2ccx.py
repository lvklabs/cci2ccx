#!/usr/bin/python

import re
import sys


def parse_method_params_decl(s, a):
    """Parses Objective-C method parameters"""

    method_params_regex = r"\s*"
    method_params_regex += r"(?P<method_name_cont>\w*)\s*:\s*"        # method name continuation
    method_params_regex += r"\((?P<param_type>\w+)\)\s*"              # parameter type
    method_params_regex += r"(?P<param_name>\w+)"                     # parameter name
    method_params_regex += r"(?P<tail>.*)"

    m = re.search(method_params_regex, s, re.DOTALL)

    if m:
        d = m.groupdict()

        tail = d.pop("tail")

        a.append(d)

        parse_method_params_decl(tail, a)


def to_cpp_method_params_decl(d):
    """Returns a string with C++ methods parameters constructed from dictionary d"""

    s = d["params"]
    pdecls = []
    parse_method_params_decl(s, pdecls)

    cpp = ""
    for pdecl in pdecls:
        if cpp != "":
            cpp += ", "
        cpp += "{param_type} {param_name}".format(**pdecl)

    d["params"] = cpp


def parse_class_methods_decl(s, a):
    """Parses Objective-C class method"""

    methods_decl_regex = r"\s*"
    methods_decl_regex += r"(?P<method_type>[+-])\s*"         # method type i.e. class or instance
    methods_decl_regex += r"\((?P<return_type>\w+)\)\s*"      # method return type
    methods_decl_regex += r"(?P<name>\w+)\s*"                 # method name
    methods_decl_regex += r"(?P<params>.*?);\s*"              # method parameters
    methods_decl_regex += r"(?P<tail>.*)"

    m = re.search(methods_decl_regex, s, re.DOTALL)

    if m:
        d = m.groupdict()

        tail = d.pop("tail")

        if d["method_type"] == "+":
            d["method_type"] = "static "
        else:
            d["method_type"] = ""

        to_cpp_method_params_decl(d)

        a.append(d)

        parse_class_methods_decl(tail, a)


def to_cpp_class_methods_decl(d):
    """Returns a string with C++ method declarations constructed from dictionary d"""
    s = d["class_methods"]
    mdecls = []
    parse_class_methods_decl(s, mdecls)

    cpp = ""
    for mdecl in mdecls:
        cpp += "    {method_type}{return_type} {name}({params});\n".format(**mdecl)

    d["class_methods"] = cpp


def parse_class_decl(s):
    """Parses Objective-C class declaration"""
    class_decl_regex = r"(?P<head>.*?)"
    class_decl_regex += r"@interface\s+(?P<class_name>\w+)"    # class name
    class_decl_regex += r"\s*:\s*(?P<super_class>\w+)\s*"      # super class
    class_decl_regex += r"({(?P<class_attrs>[^}]*)})?"         # class attributes
    class_decl_regex += r"(?P<class_methods>.*?)"              # class methods
    class_decl_regex += r"@end"                                # class end
    class_decl_regex += r"(?P<tail>.*)"

    m = re.search(class_decl_regex, s, re.DOTALL)

    return m


def to_cpp_class_decl(d):
    """Returns a string with C++ class declaration constructed from dictionary d"""
    to_cpp_class_methods_decl(d)

    cpp = """using namespace cocos2d;

class {class_name} : public {super_class}
{{
{class_attrs}
public:
    bool virtual init();
    static {class_name}* create();

{class_methods}
}};
""".format(**d)

    return cpp


def add_macro_guard(s, filename):
    """Adds C-style macro guard:"""

    macro_guard = "_" + re.sub('[^a-zA-Z]', '_', filename).upper() + "_"

    cpp = """#ifndef {macro}
#define {macro}
{source}
#endif //{macro}
""".format(macro=macro_guard, source=s)

    return cpp


def translate_header(filename):
    """Translates objective-C header to C++ header"""

    f = open(filename, 'r')
    objc = f.read()
    f.close()

    cpp = ""

    while objc != "":
        m = parse_class_decl(objc)
        if m:
            d = m.groupdict()
            cpp += d.pop("head")
            cpp += to_cpp_class_decl(d)
            objc = d.pop("tail")
        else:
            cpp += objc
            objc = ""

    cpp = cpp.replace("#import", "#include")
    cpp = add_macro_guard(cpp, filename)

    return cpp


def translate_source(filename):
    """Translates objective-C source code to C++ source code"""
    cpp = ""

    # TODO

    return cpp


def cci2ccx():
    if len(sys.argv) != 2:
        print "Syntax: " + sys.argv[0] + " <header_file>"
        return 1

    filename = sys.argv[1]

    if filename.endswith(".h"):
        cpp = translate_header(filename)
        print cpp
        return 0
    elif filename.endswith(".m"):
        #cpp = translate_source(filename)
        print "Error: Only header files are currently supported."
        return 1
    else:
        print "Error: Unknown file extension."
        return 1


def main():
    cci2ccx()


if __name__ == '__main__':
    main()
