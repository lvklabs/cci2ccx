#!/usr/bin/env python

import re
import optparse
from pprint import pprint
from collections import defaultdict
from string import Template


class cci2ccx(object):

    __cls_name = r'\s+(?P<class_name>\w+)'
    __cls_methods = r'(?P<class_methods>.*?)'
    __cls_end = '(?:@end))'
    __cls_super_class = '(?P<super_class>\w+)'
    __cls_attr = '({(?P<class_attrs>[^}]*)})'
    __class_impl_regex = r'(?P<class>(?:@implementation)' + __cls_name +\
                         __cls_methods + __cls_end

    __class_interface_regex = r'(?P<class>(?:@interface)' + __cls_name\
                        + '\(\)' + __cls_methods + __cls_end

    __class_decl_regex = '(?P<class>@interface' + __cls_name + '\s*:\s*' +\
                     __cls_super_class + '\s*' + __cls_attr + '?' + \
                      __cls_methods + __cls_end

    __type = r'(?P<type>[+-])'
    __return_type = '(?P<return_type>\w*?\*?)'
    __name = '(?P<method_name>\w*?)'
    __params = '(?P<params>:.*?)?'
    __method_decl_regex_wo_dots = r'(?:' + __type + '\s*\(' + __return_type +\
                                 '\))\s*' + __name + __params
    __method_decl_regex = __method_decl_regex_wo_dots + r';'
    __method_impl_regex = __method_decl_regex_wo_dots +\
                                r'(?:^{(?P<body>.*?)^}$)'

    __initial_comment_regex = r'(?P<initial_comment>^//.*//\n)'

    __import_block = '(?P<import_block>(?:^#import\ "\S*"(.*#import\ "\S*")?))'

    __define_block = r'(?P<define_block>#define(?:\ .*?){2}$)'

    __param_regex = r'\((?P<param_type>\w+)\)\s*(?P<param_name>\w+)'

    __attr_regex = r'(?P<attr_type>\w+)\ \s*(?P<attr_name>\*?\w+);'

    __regex_dict = {'classes_impl': {'regex': __class_impl_regex,
                                      'method_regex': __method_impl_regex},
                  'interface_impl': {'regex': __class_interface_regex,
                                      'method_regex': __method_decl_regex},
                    'classes_decl': {'regex': __class_decl_regex,
                                      'method_regex': __method_decl_regex}}

    def __init__(self):
        self._classes = defaultdict(lambda: defaultdict(lambda: {}))

        self.header_init_comment = ''
        self.header_include_block = ''
        self.header_defines = ''
        self.source_init_comment = ''
        self.source_include_block = ''
        self.source_defines = ''

    #def __str__(self):
        #return ""

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def print_regex(self, regex_name_list):
        #for k, v in cci2ccx.__regex_dict.iteritems():
        for name in regex_name_list:
            v = cci2ccx.__regex_dict[name]
            for key, value in v.iteritems():
                print name, '\t', key, '\t', value
                print name, '\t', key, 'without names\t ',\
                             re.sub('P<\w*>', ':', value)

    def parse_source(self, objc):
        self.parse(objc, 'source', ['classes_impl', 'interface_impl'])
        pass

    def parse_header(self, objc):
        self.parse(objc=objc, filetype='header',
                     regex_name_list=['classes_decl'])
        pass

    def parse(self, objc, filetype, regex_name_list):
        #print regex_name_list

        self.print_regex(regex_name_list)

        source = self.preprocess(objc)
        source = self.parse_initial_comment(source, filetype)
        source = self.parse_include(source, filetype)
        source = self.parse_define(source, filetype)
        source = self.parse_classes(source, regex_name_list)
        self.save_not_parsed(filetype, source)

    def parse_initial_comment(self, source, filetype):
        return self.parse_regex(source, cci2ccx.__initial_comment_regex,
                                filetype + '_init_comment')

    def parse_include(self, source, filetype):
        return self.parse_regex(source, cci2ccx.__import_block,
                                filetype + '_include_block')

    def parse_define(self, source, filetype):
        return self.parse_regex(source, cci2ccx.__define_block,
                                filetype + '_defines')

    def parse_regex(self, source, regex, attrname):
        rgx = re.compile(regex, re.DOTALL | re.MULTILINE)

        source_text = source
        for m in rgx.finditer(source):
            #print attrname, m.group()
            setattr(self, attrname, m.group())
            source_text = rgx.sub((lambda x: ''), source_text)

        return source_text

    def parse_classes(self, source, type_list):
        '''process classes or interfaces
        blocks of code as
        "@implementation class_name  -- OR -- @interface class_name()
        ...
        @end"

        @params
        @source: source file (ie .ccp) as string
        @type_list: list of sections types to process
        '''
        body = source
        for t in type_list:
            regex = cci2ccx.__regex_dict[t]['regex']
            method_regex = cci2ccx.__regex_dict[t]['method_regex']
            rgx = re.compile(regex, re.DOTALL | re.MULTILINE)

            for m in rgx.finditer(body):
                class_name = m.groupdict()['class_name']
                class_body = m.groupdict()['class_methods']
                class_attrs = m.groupdict().get('class_attrs')
                super_class = m.groupdict().get('super_class')

                if not self._classes[class_name].get('class_methods'):
                    self._classes[class_name]['class_methods'] \
                        = defaultdict(lambda: {})

                if class_attrs or super_class:
                    class_attrs = self.parse_attr(class_attrs)
                    self.add_class(class_name, class_attrs, super_class)

                body = rgx.sub(self.process_class(class_name,
                                            class_body, method_regex, t), body)
        return body

    def process_class(self, class_name, class_body, method_regex, cls_type):

        not_parsed = self.parse_methods(class_name, class_body, method_regex,
                                        cls_type)
        self._classes[class_name]['not_parsed'] = not_parsed
        return ''

    def parse_methods(self, class_name, class_body, method_regex, cls_type):

        rgx = re.compile(method_regex, re.DOTALL | re.MULTILINE)
        body = class_body

        for m in rgx.finditer(class_body):
            body = rgx.sub(self.process_method(class_name, m, cls_type), body)

        return body

    def process_method(self, class_name, m, cls_type):

        method_data = m.groupdict()
        method_params = m.groupdict()['params']

        if method_params and method_params != '\n':
            method_data['params'] = self.parse_method_params(method_params)
        else:
            method_data['params'] == ''

        if cls_type == 'interface_impl':
            method_data['interface'] = True

        self.add_method_to_class(class_name, method_data)

        return ''

    #TODO: merge this next two methods into uno with regex as parameter
    def parse_method_params(self, params_string):

        rgx = re.compile(self.__param_regex, re.DOTALL | re.MULTILINE)
        param_list = []

        for m in rgx.finditer(params_string):
            param_list.append(m.groupdict())

        return param_list

    def parse_attr(self, attr_string):
        if not attr_string:
            return ''

        rgx = re.compile(self.__attr_regex, re.DOTALL | re.MULTILINE)
        attr_list = []

        for m in rgx.finditer(attr_string):
            attr_list.append(m.groupdict())

        return attr_list

    def add_class(self, class_name, class_attrs, super_class):

        self._classes[class_name]['class_attrs'] = class_attrs
        self._classes[class_name]['super_class'] = super_class

    def add_method_to_class(self, class_name, method_data):
        method_name = method_data['method_name']

        assert method_data
        prev_dict = self._classes[class_name]['class_methods'][method_name]

        if prev_dict:
            self.assert_dicts_new_data_equal(prev_dict, method_data)

        self._classes[class_name]['class_methods'][method_name]\
                            .update(method_data)

    def save_not_parsed(self, filetype, source):
        #save not parsed part of file
        setattr(self, filetype, source)
        #print "not parsed of %s : \n %s" % (filetype, source)

    def preprocess(self, source):
        return re.sub("\t", '    ', source)

    def assert_dicts_new_data_equal(self, prev_dict, new_dict):
        '''
        if we already parse the method, must check if all the data is
        consistent to the previus parsed data
        '''
        #TODO: fix comparasion some times has \n at the end some times doesn't
        for k, v in new_dict.iteritems():
                if prev_dict.get(k):
                    if isinstance(prev_dict.get(k), str):
                        p_value = re.sub('\n', '', prev_dict.get(k))
                        n_value = re.sub('\n', '', prev_dict.get(k))
                        #print k, "has'", prev_dict.get(k), "\'new value \'", v
                    assert p_value == n_value

    def list_clases_names(self):
        print "classes list:\n"
        for cls, data in self._classes.iteritems():
            print "class name", cls, "\n"
            #print self.list_methods_of_class(cls)
            pprint(dict(self._classes[cls]))
            #pprint(data)

    def get_classes(self):
        for k, v in self._classes.iteritems():
            yield k, v

    def get_methods(self, class_name):
        for k, v in self._classes[class_name].iteritems():
            yield k, v

    def list_methods_of_class(self, class_name):
        for k, v in self._classes[class_name].iteritems():
                print "has method:", k, "\n"

###############################################################################


class parsed_to_cpp(object):

    def __init__(self, data):
        self.data = data
        #print self.data.init_comment

    def fill_template(self, template_name, data):
        f = open('./tmpl/' + template_name, 'r')
        template = f.read()
        f.close()
        return Template(template).safe_substitute(data)

    def construct_header(self):

        header = self.data.header_init_comment + '\n'
        header += self.data.header_include_block.replace(
                        "#import", "#include") + '\n'
        header += self.data.header_defines + '\n'
        header += 'not parsed \n -->'
        header += self.data.header.strip('\n') + '\n'
        header += '<-- not parsed \n'
        header += self.construct_clases_header()

        #header = self.add_macro_guard(header, filename)
        return header

    def construct_source(self):

        pprint(self.data.__dict__)
        source = self.data.source_init_comment + '\n'
        source += self.data.source_include_block.replace(
                        "#import", "#include") + '\n'
        source += self.data.source_defines + '\n'
        source += 'not parsed \n -->'
        source += self.data.source.strip('\n') + '\n'
        source += '<-- not parsed \n'
        source += self.construct_clases_source()

        #source = self.add_macro_guard(header, filename)
        return source

    def construct_clases_header(self):
        '''useing the data from data.get_classes() create the string
        representing the parsed class in cpp
        '''
        classes = ''
        for k, v in self.data.get_classes():

            v = dict(v)
            v['class_name'] = k
            #pprint(dict(v['class_methods']))
            class_methods_dict = dict(v['class_methods'])

            v['class_methods_private'] = self.get_methods(class_methods_dict,
                                                            True)
            v['class_methods_public'] = self.get_methods(class_methods_dict,
                                                            False)
            if v.get('class_attrs'):
                v['class_attrs'] = self.construct_attr(v['class_attrs'])
            else:
                v['class_attrs'] = ''

            classes += self.fill_template('class_decl_template', dict(v))

        return classes

    def construct_clases_source(self):
        '''useing the data from data.get_classes() create the string
        representing the parsed class in cpp
        '''
        classes = ''
        for k, v in self.data.get_classes():

            class_methods_dict = dict(v['class_methods'])
            for method, data in class_methods_dict.iteritems():
                data['class_name'] = k
                if data.get('params'):
                    data['params'] = self.construct_method_params(
                                        data.get('params'))
                else:
                    data['params'] = ''
                classes += self.fill_template('method_def_template', data)

        return classes

    def construct_declaration(self, methods):
        '''construct and translate methods from parsed method data'''
        #TODO: translate types
        #TODO: maybe order methods by name or other criteria

        method_decl = ''

        for k, v in methods.iteritems():
            method_decl += '    '

            if v['type'] == '+':
                method_decl += 'static '
            method_decl += v['return_type'] + ' '
            method_decl += v['method_name']
            if v.get('params'):
                method_decl += '(' +\
                                self.construct_method_params(
                                    v.get('params')) + ')'

            method_decl += ';\n'

        return method_decl

    def construct_method_params(self, param_list):
        '''take a list of dicts {'param_name': 'someName',
                                'param_type': 'someType'}

        and return correct cpp formated params
        '''
        params_string = ''
        for p in param_list:
            params_string += self.translate_type(p['param_type']) + ' ' +\
                             p['param_name'] + ', '

        return params_string.rstrip(', ')

    def construct_attr(self, attr_list):
        '''take a list of dicts {'attr_name': '_layerTime',
                                'attr_type': 'ccTime'}

        @returns a string with attributes of the class translated to cpp
        '''
        attr_string = ''
        for a in attr_list:
            attr_string += '    '
            attr_string += self.translate_type(a['attr_type']) + ' ' +\
                           a['attr_name'] + ';\n'

        return attr_string

    def add_macro_guard(self, source, filename):
        """Adds C-style macro guard:
        #ifndef XXX
        #define XXX
        ...
        #endif"""

        macro_guard = "_" + re.sub('[^a-zA-Z]', '_', filename).upper() + "_"
        data = {'macro': macro_guard, 'source': source}

        return self.fill_template(template_name='macro_guard_template',
                                  data=data)

    def get_methods(self, class_methods_dict, from_interface):
        #TODO: DRY it
        if from_interface:
            #Recover methods parsed form interface ie private methods
            private_methods = {k: v for (k, v) in
                                class_methods_dict.iteritems()
                                if v.get('interface')}
            if private_methods:
                return self.construct_declaration(private_methods)
            else:
                return ''
        else:
            #Recover methods NOT parsed form interface ie private methods
            public_methods = {k: v for (k, v) in
                                class_methods_dict.iteritems()
                                if not v.get('interface')}

            return self.construct_declaration(public_methods)

    def translate_type(self, objc_type):
        '''takes an objective-c type and translate it to cpp equivalent'''
        #TODO:
        return objc_type

    def write_file(self):
        pass

###############################################################################

if __name__ == '__main__':
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--header", dest="header",
        help="header file")
    opt_parser.add_option("--source", dest="source",
        help="source file, must provide one")
    (options, args) = opt_parser.parse_args()
    if not options.source:
        exit("not source indicated, \n please use -h to more help")

    options = vars(options)

    f = open(options['source'], 'r')
    source = f.read()
    f.close()

    f = open(options['header'], 'r')
    header = f.read()
    f.close()

    ci2cx = cci2ccx()
    ci2cx.parse_source(source)
    ci2cx.parse_header(header)
    #ci2cx.list_clases_names()
    ptc = parsed_to_cpp(ci2cx)
    #print ptc.construct_header()
    print ptc.construct_source()
