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
A module wich parse an iphone objective-c source(.m) and header(.h) and save
the estructure inside

Primary thinked for code using cocos2d library for game develop, but it should
word for any objective-c code
"""

import re
from pprint import pprint
from collections import defaultdict


class ParseObjc(object):

    __cls_name = r'\s+(?P<class_name>\w+)'
    __cls_methods = r'(?P<class_methods>.*?)'
    __cls_end = '(?:^@end))'
    __cls_super_class = '(?P<super_class>\w+)'
    __cls_attr = '({(?P<class_attrs>[^}]*)})'
    __class_impl_regex = r'(?P<class>(?:^@implementation)' + __cls_name +\
                         __cls_methods + __cls_end

    __class_interface_regex = r'(?P<class>(?:^@interface)' + __cls_name\
                        + '\s?\(\)' + __cls_methods + __cls_end

    __class_decl_regex = '(?P<class>^@interface' + __cls_name + '\s*:\s*' +\
                     __cls_super_class + '\s*' + __cls_attr + '?' + \
                      __cls_methods + __cls_end

    __type = r'(?P<type>[+-])'
    __return_type = '\((?P<return_type>\w*?\ ?\*?\ ?)\)'
    __name = '(?P<method_name>\w*?)'
    __params = '(?P<params>:.*?)?'
    __method_decl_regex_wo_dots = r'(?:' + __type + '\s*' + __return_type +\
                                 ')\s*' + __name + '\s*' + __params
    __method_decl_regex = __method_decl_regex_wo_dots + r';'
    __method_impl_regex = '(?P<original_method>' +\
                            __method_decl_regex_wo_dots +\
                            r'(?:^{(?P<body>.*?)^}\ *$)' + ')'

    __initial_comment_regex = r'(?P<initial_comment>^//.*//\n)'

    __import_block = '(?P<import_block>(?:^#import\ "\S*"(.*#import\ "\S*")?))'

    __define_block = r'(?P<define_block>#define(?:\ .*?){2}$)'

    __param_regex = r'\((?P<param_type>\w+\s*\*?)\)\s*(?P<param_name>\w+)'

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

    def __str__(self):
        string = ''
        for cls, cdata in self._classes.iteritems():
            string += cls + '\n'
            string += '\t BaseClassName \n \t\t' + cdata['super_class'] + '\n'
            string += '\t methods_count \n \t\t' +\
                     str(cdata['methods_count']) + '\n'
            string += '\t class atributes \n \t\t' +\
                     str(cdata['class_attrs']) + '\n'

            string += 'Methods: \n\n'
            for mkey, mdata in cdata['class_methods'].iteritems():
                string += '\t ' + mkey + '\n'
                if mkey == 'getItemsOwnedAtLevel':
                    string += str(mdata)
                #+ '\n --SART-- \n \t\t' + '\n--END--\n'
                         #str(cdata['class_methods']) +\
            #string += 'Methods END \n\n'

            string += '\n -- Not parsed in header START --\n \t\t' +\
                 cdata['header']['not_parsed'].strip('\n') + '\n' +\
                  '--Not parsed in header END --\n\n'
            string += '\n-- Not parsed in source START --\n \t\t' +\
                 cdata['source']['not_parsed'].strip('\n') + '\n' +\
                  '--Not parsed in source END --\n\n'

        return string

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def print_regex(self):
        regex_name_list = ['classes_impl', 'interface_impl',
                              'classes_decl']
        self.print_regex_list(regex_name_list)

    def print_regex_list(self, regex_name_list):

        for name in regex_name_list:
            v = ParseObjc.__regex_dict[name]
            for key, value in v.iteritems():
                print name, '\t', key, '\t', value
                print name, '\t', key, 'without names\t ',\
                             re.sub('P<\w*>', ':', value)
            print '\n'

    def parse_source(self, objc):
        self.parse(objc, 'source', ['classes_impl', 'interface_impl'])
        pass

    def parse_header(self, objc):
        self.parse(objc=objc, filetype='header',
                     regex_name_list=['classes_decl'])
        pass

    def parse(self, objc, filetype, regex_name_list):
        #self.print_regex(regex_name_list)  #for debuging print the regex

        source = self.preprocess(objc)
        source = self.parse_initial_comment(source, filetype)
        source = self.parse_include(source, filetype)
        source = self.parse_define(source, filetype)
        source = self.parse_classes(source, regex_name_list, filetype)

        self.save_not_parsed(filetype, source)

    def parse_initial_comment(self, source, filetype):
        return self.parse_regex(source, ParseObjc.__initial_comment_regex,
                                filetype + '_init_comment')

    def parse_include(self, source, filetype):
        return self.parse_regex(source, ParseObjc.__import_block,
                                filetype + '_include_block')

    def parse_define(self, source, filetype):
        return self.parse_regex(source, ParseObjc.__define_block,
                                filetype + '_defines')

    def parse_regex(self, source, regex, attrname):
        rgx = re.compile(regex, re.DOTALL | re.MULTILINE)

        source_text = source
        for m in rgx.finditer(source):
            setattr(self, attrname, m.group())
            source_text = rgx.sub((lambda x: ''), source_text)

        return source_text

    def parse_classes(self, source, type_list, filetype):
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
            regex = ParseObjc.__regex_dict[t]['regex']
            method_regex = ParseObjc.__regex_dict[t]['method_regex']
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
                                            class_body, method_regex, t,
                                            filetype), body)
        return body

    def process_class(self, class_name, class_body, method_regex, cls_type,
                     filetype):

        not_parsed = self.parse_methods(class_name, class_body, method_regex,
                                        cls_type)

        self._classes[class_name][filetype]['not_parsed'] = not_parsed
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
        #else:
            #method_data['interface'] = False


        method_data['method_name_key'] = self.contruct_method_name_key(method_data['method_name'],
                                     method_params)

        #print method_data['method_name_key']
        self.add_method_to_class(class_name, method_data)

        return ''

    #TODO: merge this next two methods into uno with regex as parameter
    def parse_method_params(self, params_string):
        #print params_string

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
        method_name = method_data['method_name_key']

        assert method_data
        prev_dict = self._classes[class_name]['class_methods'][method_name]

        #keep order of methods
        methods_count = self._classes[class_name].get('methods_count')

        if not methods_count:
            self._classes[class_name]['methods_count'] = 0

        if prev_dict:
            self.assert_dicts_new_data_equal(prev_dict, method_data)
            method_data['order'] = prev_dict['order']
            #print "same", method_data.get('order')
        else:
            #print prev_dict, '\n\n'
            self._classes[class_name]['methods_count'] += 1
            method_data['order'] =\
                self._classes[class_name]['methods_count']

        #print class_name, method_name, method_data['order']

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
        #TODO: insted of re.sub use strim
        for k, v in new_dict.iteritems():
                if prev_dict.get(k):
                    if isinstance(prev_dict.get(k), str):
                        p_value = re.sub('\n', '', prev_dict.get(k))
                        n_value = re.sub('\n', '', prev_dict.get(k))
                        #print k, "has'", prev_dict.get(k), "\'new value \'", v
                    assert p_value == n_value

    def contruct_method_name_key(self, name, params_string):
        if not params_string:
            return name
        rgx = re.compile('(?P<partname>\w+):', re.DOTALL | re.MULTILINE)

        for m in rgx.finditer(params_string):
            name += m.groupdict()['partname']
        return name

    def list_clases_names(self):
        print "classes list:\n"
        for cls, data in self._classes.iteritems():
            print "class name", cls, "\n"
            #print self.list_methods_of_class(cls)
            pprint(dict(self._classes[cls]))

    def get_classes(self):
        for k, v in self._classes.iteritems():
            yield k, v

    def get_methods(self, class_name):
        #for k, v in self._classes[class_name].iteritems():
            #yield k, v

        for k, v in sorted(self._classes[class_name].iteritems(),
                     key=lambda (k,v): v['order']):
            yield k, v

    def list_methods_of_class(self, class_name):
        for k, v in self._classes[class_name].iteritems():
                print "has method:", k, "\n"

    #def order(self, v):
        #return v['order']

if __name__ == '__main__':
    parserObjc = ParseObjc()
    parserObjc.print_regex()