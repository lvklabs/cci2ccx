#
# Copyright (C) 2012 LVK labs
#
# This file is part of LVK cci2ccx tool.
#
# LVK cci2ccx is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LVK cci2ccx is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LVK cci2ccx. If not, see <http://www.gnu.org/licenses/>.

"""
A module to translate a ParseObjc object to c++ using cocos2d-x as primary
library


"""

import re
from pprint import pprint
from collections import defaultdict
from string import Template


class CppTranslate(object):

    def __init__(self, parseObjc):
        self.data = parseObjc
        self.header_file_name = None

    def fill_template(self, template_name, data):
        f = open('./tmpl/' + template_name, 'r')
        template = f.read()
        f.close()
        return Template(template).safe_substitute(data)

    def construct_header(self):

        header = self.data.header_include_block.replace(
                        "#import", "#include") + '\n'
        header += self.data.header_defines + '\n'
        header += self.not_parsed(self.data.header)
        header += self.construct_clases_header()

        header = self.add_macro_guard(header, self.header_file_name)

        header = ''.join([self.data.header_init_comment, '\n', header, '\n'])

        return header

    def construct_source(self):

        source = self.data.source_include_block.replace(
                        "#import", "#include") + '\n' * 2
        source += self.data.source_defines + '\n' * 2
        source += self.not_parsed(self.data.source)
        source += self.construct_clases_source()

        source = self.add_macro_guard(source, self.header_file_name)

        source = ''.join([self.data.source_init_comment, '\n', source, '\n'])

        return source

    def construct_clases_header(self):
        """useing the data from data.get_classes() create the string
        representing the parsed class in cpp
        """
        classes = ''
        for k, v in self.data.get_classes():

            v = dict(v)
            v['class_name'] = k
            class_methods_dict = dict(v['class_methods'])

            v['class_methods_private'] = self.get_methods(class_methods_dict,
                                                            True)
            v['class_methods_public'] = self.get_methods(class_methods_dict,
                                                            False)
            if v.get('class_attrs'):
                v['class_attrs'] = self.construct_attr(v['class_attrs'])
            else:
                v['class_attrs'] = ''

            v['not_parsed'] = v['not_parsed'].strip('\n')

            if v['not_parsed']:
                v['not_parsed'] = "/* \n not parsed ---------->\n" +\
                         v['not_parsed'] + "\n<------------ not parsed \n*/ "

            classes += self.fill_template('class_decl_template', dict(v))

        return classes

    def construct_clases_source(self):
        """
        using the data from data.get_classes() create the string
        representing the parsed class in cpp
        """
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
        """
        construct and translate methods from parsed method data
        """
        #TODO: translate types
        #TODO: maybe order methods by name or other criteria

        method_decl = ''

        for k, v in methods.iteritems():
            method_decl += '    '

            if v['type'] == '+':
                method_decl += 'static '
            method_decl += self.translate_type(v['return_type']) + ' '
            method_decl += v['method_name']
            if v.get('params'):
                method_decl += '(' +\
                                self.construct_method_params(
                                    v.get('params')) + ')'
            else:
                method_decl += '()'

            method_decl += ';\n'

        return method_decl

    def construct_method_params(self, param_list):
        """
        take a list of dicts {'param_name': 'someName',
                                'param_type': 'someType'}

        and return correct cpp formated params
        """
        params_string = ''

        for p in param_list:
            params_string += self.translate_type(p['param_type']) + ' ' +\
                             p['param_name'] + ', '

        return params_string.rstrip(', ')

    def construct_attr(self, attr_list):
        """
        take a list of dicts {'attr_name': '_layerTime',
                                'attr_type': 'ccTime'}

        @returns a string with attributes of the class translated to cpp
        """
        attr_string = ''
        for a in attr_list:
            attr_string += '    '
            attr_string += self.translate_type(a['attr_type']) + ' ' +\
                           a['attr_name'] + ';\n'

        return attr_string

    def add_macro_guard(self, source, filename):
        """
        Adds C-style macro guard:
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

    def not_parsed(self, not_parsed_source):
        code = ''
        not_parsed = not_parsed_source.strip('\n')

        if not_parsed:
            code += '/* not parsed \n -->'
            code += not_parsed + '\n'
            code += '<-- not parsed */' + '\n' * 2
        else:
            print not_parsed
        return code

    def set_header_name(self, header_file_name):
        self.header_file_name = header_file_name
        #setattr(self, header_file_name, header_file_name)
        pass

    def translate_type(self, objc_type):
        """
        takes an objective-c type and translate it to cpp equivalent
        """

        equivalent_dict = ({'YES': 'true', 'NO': 'false', 'BOOL': 'bool',
            'CGSize': 'CCSize', 'CGRect': 'CCRect', 'CGPoint': 'CCPoint',
            'CGFloat': 'CCFloat', 'NSString': 'CCString',
            'NSMutableDictionary': 'CCDictionary',
            'NSDictionary': 'CCDictionary',
            'NSObject': 'CCObject', 'NSInteger': 'CCInteger',
            'NSUInteger': 'CCInteger'})

        if objc_type in equivalent_dict.keys():
            return equivalent_dict[objc_type]
        else:
            return objc_type
