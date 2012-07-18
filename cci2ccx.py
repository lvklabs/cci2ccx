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

    class_decl_regex += r"@interface\s+(?P<class_name>\w+)"
    class_decl_regex += r"\s*:\s*(?P<super_class>\w+)\s*"
    class_decl_regex += r"({(?P<class_attrs>[^}]*)})?"
    class_decl_regex += r"(?P<class_methods>.*?)"
    class_decl_regex += r"@end"

    class_decl_regex += r"(?P<tail>.*)"

    m = re.search(class_decl_regex, s, re.DOTALL)

    return m


def expand_cpp_class_methods_decl(m):
    # TODO
    return m


def expand_cpp_class_decl(m):
    expand_cpp_class_methods_decl(m)

    cpp = """
using namespace cocos2d;

class {class_name} : public {super_class}
{{
{class_attrs}
public:
   bool virtual init();
   static class_name* create();

/* FIXME ObjC Methods: {class_methods} */

}};
""".format(**m.groupdict())

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
            cpp += expand_cpp_class_decl(m)
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

