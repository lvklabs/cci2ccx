#!/usr/bin/python

import re
import sys


CPP_MACRO_GUARD_TEMPLATE = \
"""#ifndef {macro}
#define {macro}
{source}
#endif //{macro}
"""

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

CPP_METHOD_DEF_TEMPLATE = \
"""{return_type} {class_name}::{method_name}(/* FIXME {params} */)
{{
/* FIXME:
{body}
*/
}}
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

        f = open(filename, 'r')
        objc = f.read()
        f.close()

        cpp = ""

        while objc != "":
            m = self.parse_class_def(objc)
            if m:
                d = m.groupdict()
                cpp += d.pop("head")
                cpp += self.to_cpp_class_def(d)
                objc = d.pop("tail")
            else:
                cpp += objc
                objc = ""

        cpp = cpp.replace("#import", "#include")

        return cpp

    ###############################################################################################

    def parse_class_decl(self, s):
        """Parses a Objective-C class declaration:
        @interface class_name : super_class
        ...
        @end
        """

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

        self.to_cpp_methods_decl(d)

        cpp = CPP_CLASS_DECL_TEMPLATE.format(**d)

        return cpp

    def parse_methods_decl(self, s, a):
        """Parses a Objective-C method declaration
        - (return_type) instance_method:(type)param ...
        + (return_type) class_method:(type)param ...
        """

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

            self.parse_methods_decl(tail, a)

    def to_cpp_methods_decl(self, d):
        """Returns a string with C++ method declarations constructed from dictionary d"""

        s = d["class_methods"]
        mdecls = []
        self.parse_methods_decl(s, mdecls)

        cpp = ""
        for mdecl in mdecls:
            cpp += "    {method_type}{return_type} {name}({params});\n".format(**mdecl)

        d["class_methods"] = cpp

    def parse_method_params_decl(self, s, a):
        """Parses Objective-C method parameters:
        class_name_cont:(param_type)param_name
        """

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

    ###############################################################################################

    def parse_class_def(self, s):
        """Parses a Objective-C class definition:
        @implementation class_name
        ...
        @end
        """

        class_def_regex = r"(?P<head>.*?)"
        class_def_regex += r"@implementation\s+(?P<class_name>\w+)"   # class definition start
        class_def_regex += r"(?P<methods>.*?)"                        # class methods
        class_def_regex += r"@end"                                    # class definition end
        class_def_regex += r"(?P<tail>.*)"

        m = re.search(class_def_regex, s, re.DOTALL)

        if m:
            print m.group("head")    # FIXME remove print

            methods = []
            self.parse_method_def(m.group("methods"), methods)

            for method in methods:
                method["class_name"] = m.group("class_name")
                print CPP_METHOD_DEF_TEMPLATE.format(**method)     # FIXME remove print

        return m

    def to_cpp_class_def(self, d):
        """Returns a string with C++ class definition constructed from dictionary d"""

        # TODO

        return ""

    def parse_method_def(self, s, a):
        """Parses Objective-C method definitions
        - (return_type) instance_method:(type)param { ... }
        + (return_type) class_method:(type)param { ... }
        """

        methods_def_regex = r"\s*"
        methods_def_regex += r"(?P<method_type>[+-])\s*"         # m. type i.e. class or instance
        methods_def_regex += r"\((?P<return_type>\w+)\)\s*"      # method return type
        methods_def_regex += r"(?P<method_name>\w+)\s*"          # method name
        methods_def_regex += r"(?P<params>.*?)\s*"               # method parameters
        methods_def_regex += r"(?P<body_unbound>{.*)"            # method body + tail

        m = re.search(methods_def_regex, s, re.DOTALL)

        if m:
            d = m.groupdict()

            # TODO parse parameters

            body_unbound = d.pop("body_unbound")

            l = self.parse_method_body(body_unbound)

            body = l[0]
            tail = l[1]

            d["body"] = body
            a.append(d)

            self.parse_method_def(tail, a)

    def parse_method_body(self, s):
        """Parses a method body:
        {
        ... body ...
        }
        ... tail ...
        Returns [body, tail]
        """

        brace_count = 0
        body_started = 0
        i = 0

        for i, c in enumerate(s):
            if brace_count == 0 and body_started == 1:
                break
            if c == '{':
                brace_count += 1
                body_started = 1
            elif c == '}':
                brace_count -= 1

        body = s[1:(i - 1)]
        tail = s[(i + 1):len(s)]

        return [body, tail]


###################################################################################################


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
        cpp_source = cci2ccx().translate_source(filename)
        #print cpp_source
        return 0
    else:
        print "Error: Unknown file extension."
        return 1


if __name__ == '__main__':
    main()
