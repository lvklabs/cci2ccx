#!/usr/bin/python

import re
import sys

CPP_CLASS_DECL_TEMPLATE = \
"""using namespace cocos2d;

class {class_name} : public {super_class}
{{
{class_attrs}
public:
    bool virtual init();
    static {class_name}* create();

{class_methods}
}};
"""

CPP_MACRO_GUARD_TEMPLATE = \
"""#ifndef {macro}
#define {macro}
{source}
#endif //{macro}
"""


class cci2ccx:

    def translate_header(self, filename):
        """Translates objective-C header to C++ header"""

        f = open(filename, 'r')
        objc = f.read()
        f.close()

        cpp = ""

        while objc != "":
            m = self.parse_class_decl(objc)
            if m:
                d = m.groupdict()
                cpp += d.pop("head")
                cpp += self.to_cpp_class_decl(d)
                objc = d.pop("tail")
            else:
                cpp += objc
                objc = ""

        cpp = cpp.replace("#import", "#include")
        cpp = self.add_macro_guard(cpp, filename)

        return cpp

    def translate_source(self, filename):
        """Translates objective-C source code to C++ source code"""
        cpp = ""

        # TODO

        return cpp

    def parse_class_decl(self, s):
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

    def to_cpp_class_decl(self, d):
        """Returns a string with C++ class declaration constructed from dictionary d"""

        self.to_cpp_class_methods_decl(d)

        cpp = CPP_CLASS_DECL_TEMPLATE.format(**d)

        return cpp

    def parse_class_methods_decl(self, s, a):
        """Parses Objective-C class method declaration"""

        methods_decl_regex = r"\s*"
        methods_decl_regex += r"(?P<method_type>[+-])\s*"         # m. type i.e. class or instance
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

            self.to_cpp_method_params_decl(d)

            a.append(d)

            self.parse_class_methods_decl(tail, a)

    def to_cpp_class_methods_decl(self, d):
        """Returns a string with C++ method declarations constructed from dictionary d"""

        s = d["class_methods"]
        mdecls = []
        self.parse_class_methods_decl(s, mdecls)

        cpp = ""
        for mdecl in mdecls:
            cpp += "    {method_type}{return_type} {name}({params});\n".format(**mdecl)

        d["class_methods"] = cpp

    def parse_method_params_decl(self, s, a):
        """Parses Objective-C method parameters"""

        method_params_regex = r"\s*"
        method_params_regex += r"(?P<method_name_cont>\w*)\s*:\s*"      # method name continuation
        method_params_regex += r"\((?P<param_type>\w+)\)\s*"            # parameter type
        method_params_regex += r"(?P<param_name>\w+)"                   # parameter name
        method_params_regex += r"(?P<tail>.*)"

        m = re.search(method_params_regex, s, re.DOTALL)

        if m:
            d = m.groupdict()

            tail = d.pop("tail")

            a.append(d)

            self.parse_method_params_decl(tail, a)

    def to_cpp_method_params_decl(self, d):
        """Returns a string with C++ methods parameters constructed from dictionary d"""

        s = d["params"]
        pdecls = []
        self.parse_method_params_decl(s, pdecls)

        cpp = ""
        for pdecl in pdecls:
            if cpp != "":
                cpp += ", "
            cpp += "{param_type} {param_name}".format(**pdecl)

        d["params"] = cpp

    def add_macro_guard(self, s, filename):
        """Adds C-style macro guard:
        #ifndef XXX
        #define XXX
        ...
        #endif"""

        macro_guard = "_" + re.sub('[^a-zA-Z]', '_', filename).upper() + "_"

        cpp = CPP_MACRO_GUARD_TEMPLATE.format(macro=macro_guard, source=s)

        return cpp


def main():
    if len(sys.argv) != 2:
        print "Syntax: " + sys.argv[0] + " <header_file>"
        return 1

    filename = sys.argv[1]

    if filename.endswith(".h"):
        cpp_header = cci2ccx().translate_header(filename)
        print cpp_header
        return 0
    elif filename.endswith(".m"):
        #cpp_source = cci2ccx().translate_source(filename)
        print "Error: Only header files are currently supported."
        return 1
    else:
        print "Error: Unknown file extension."
        return 1


if __name__ == '__main__':
    main()
