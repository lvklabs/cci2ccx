#!/usr/bin/python

import re
import sys


def add_macro_guard(s, filename):

    macro_guard = "_" + re.sub('[^a-zA-Z]', '_', filename).upper() + "_"

    cpp = "#ifndef " + macro_guard + "\n"
    cpp += "#define " + macro_guard + "\n"
    cpp += s
    cpp += "\n#endif //" + macro_guard + "\n"

    return cpp


def parse_class_decl(s):
    class_decl_regex = r"(?P<head>.*?)"
    class_decl_regex += r"@interface\s+(?P<class_name>\w+)"    # class name
    class_decl_regex += r"\s*:\s*(?P<super_class>\w+)\s*"      # super class
    class_decl_regex += r"({(?P<class_attrs>[^}]*)})?"         # class attributes
    class_decl_regex += r"(?P<class_methods>.*?)"              # class methods
    class_decl_regex += r"@end"                                # class end
    class_decl_regex += r"(?P<tail>.*)"

    m = re.search(class_decl_regex, s, re.DOTALL)

    return m


def parse_class_methods_decl(s, a):
    methods_decl_regex = r"\s*"
    methods_decl_regex += r"(?P<type>[+-])\s*"                # method type i.e. class or instance
    methods_decl_regex += r"\((?P<return_type>\w+)\)\s*"      # method return type
    methods_decl_regex += r"(?P<name>\w+)\s*"                 # method name
    methods_decl_regex += r"(?P<params>.*?);\s*"              # method parameters
    methods_decl_regex += r"(?P<tail>.*)"

    m = re.search(methods_decl_regex, s, re.DOTALL)

    if m:
        d = m.groupdict()

        if d["type"] == "+":
            d["type"] = "static "
        else:
            d["type"] = ""

        tail = d.pop("tail")
        a.append(d)

        parse_class_methods_decl(tail, a)


def expand_cpp_class_methods_decl(d):
    s = d["class_methods"]
    a = []
    parse_class_methods_decl(s, a)

    cpp = ""
    for mdecl in a:
        cpp += "    {type}{return_type} {name}(/* FIXME {params} */);\n".format(**mdecl)

    d["class_methods"] = cpp


def expand_cpp_class_decl(d):
    expand_cpp_class_methods_decl(d)

    cpp = """
using namespace cocos2d;

class {class_name} : public {super_class}
{{
{class_attrs}
public:
    bool virtual init();
    static class_name* create();

{class_methods}

}};
""".format(**d)

    return cpp


def cci2ccx():
    if len(sys.argv) != 2:
        print "Syntax: " + sys.argv[0] + " <header_file>"
        return 1

    filename = sys.argv[1]

    f = open(filename, 'r')

    objc = f.read()

    cpp = ""

    while objc != "":
        m = parse_class_decl(objc)
        if m:
            cpp += m.group("head")
            cpp += expand_cpp_class_decl(m.groupdict())
            objc = m.group("tail")
        else:
            cpp += objc
            objc = ""

    cpp = cpp.replace("#import", "#include")
    cpp = add_macro_guard(cpp, filename)

    print cpp

    return 0


#########################
cci2ccx()
#########################

