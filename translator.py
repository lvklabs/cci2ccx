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
        #print parseObjc
        self.header_file_name = None
        self.equivalent_dict = ({'YES': 'true', 'NO': 'false', 'BOOL': 'bool',
            'CGSize': 'CCSize', 'CGRect': 'CCRect', 'CGPoint': 'CCPoint',
            'CGFloat': 'CCFloat', 'NSString': 'CCString',
            'NSMutableDictionary': 'CCDictionary',
            'NSDictionary': 'CCDictionary', 'NSNumber': 'CCNumber',
            'NSObject': 'CCObject', 'NSInteger': 'CCInteger',
            'NSUInteger': 'CCInteger', 'NSSet': 'CCSet', 'UIEvent': 'CCEvent',
            'NSMutableArray': 'CCMutableArray', 'NSArray': 'CCArray',
            ' nil': ' NULL', 'ccp': 'CCPoint', 'CGPointMake': 'CCPoint',
            'self': 'this', 'NSSet': 'CCSet', 'SEL ': 'SEL_MenuHandler ',
            'UITextAlignmentCenter': 'kCCTextAlignmentCenter'})

    def fill_template(self, template_name, data):
        #TODO: don't onpen the template for each call, make it once time only
        #Implemente load template() int the initializaiton
        f = open('./tmpl/' + template_name, 'r')
        template = f.read()
        f.close()
        return Template(template).safe_substitute(data)

    def construct_header(self):

        #pprint(self.data.get_methods("GameView"))
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

        source = ''.join([self.data.source_init_comment, '\n', source, '\n'])

        return source

    def construct_clases_header(self):
        """useing the data from data.get_classes() create the string
        representing the parsed class in cpp
        """
        classes = ''
        for class_name, v in self.data.get_classes():

            v = dict(v)
            v['class_name'] = class_name

            #pprint(v)
            if v.get('class_methods'):
                class_methods_dict = dict(v.get('class_methods'))

                v['class_methods_private'] = self.get_methods(class_name,
                                                            class_methods_dict,
                                                                True)
                v['class_methods_public'] = self.get_methods(class_name,
                                                             class_methods_dict,
                                                                False)
            else:
                #TODO log this insted of print
                print "There is no method in header"
                v['class_methods_private'] = ''
                v['class_methods_public'] = ''

            if v.get('class_attrs'):
                v['class_attrs'] = self.construct_attr(v['class_attrs'])
            else:
                v['class_attrs'] = ''

            if v.get('header') and v.get('header').get('not_parsed'):
                v['not_parsed'] = v.get('header').get('not_parsed')
            else:
                v['not_parsed'] = ''

            classes += self.fill_template('class_decl_template', dict(v))

        return classes

    def construct_clases_source(self):
        """
        using the data from data.get_classes() create the string
        representing the parsed class in cpp
        """
        classes = ''
        for class_name, v in self.data.get_classes():

            not_parsed = v['source'].get('not_parsed')

            if not_parsed:
                not_parsed = not_parsed.strip('\n')

            classes += self.fill_template('class_impl_start_template',
                                        {'class_name': class_name,
                                        'not_parsed': not_parsed})

            class_methods_dict = dict(v['class_methods'])
            class_methods_dict = sorted(class_methods_dict.iteritems(),
                     key=lambda (k, v): v['order'])

            for method, data in class_methods_dict:
                data['class_name'] = class_name
                if data.get('params'):

                    data['params'] = self.construct_method_params(
                                        data.get('params'))
                else:
                    data['params'] = ''

                if data.get('body'):
                    data['body_translated'] = self.translate_method_code(
                                                            class_name,
                                                            data['body'])
                data['return_type'] = self.translate_type(data['return_type'])
                data['method_name'] = self.translate_method_name(class_name,
                                                         data['method_name'])

                classes += self.fill_template('method_def_template', data)

        return classes

    def construct_declaration(self, class_name, methods):
        """
        construct and translate methods from parsed method data
        """
        #TODO: translate types
        #TODO: maybe order methods by name or other criteria

        method_decl = ''

        if methods.get('init'):
            method_decl += '    bool virtual init();\n'
            methods.pop('init')

        for k, v in methods.iteritems():
            method_decl += '    '

            if v['type'] == '+':
                method_decl += 'static '
            method_decl += self.translate_type(v['return_type']) + ' '
            method_decl += self.translate_method_name(class_name,
                                                         v['method_name'])
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

    def get_methods(self, class_name, class_methods_dict, from_interface):
        #TODO: DRY it
        if from_interface:
            #Recover methods parsed form interface ie private methods
            private_methods = {k: v for (k, v) in
                                class_methods_dict.iteritems()
                                if v.get('interface')}

            if private_methods:
                return self.construct_declaration(class_name, private_methods)
            else:
                return ''
        else:
            #Recover methods NOT parsed form interface ie public methods
            public_methods = {k: v for (k, v) in
                                class_methods_dict.iteritems()
                                if not v.get('interface')}

            return self.construct_declaration(class_name, public_methods)

    def not_parsed(self, not_parsed_source):
        code = ''
        not_parsed = not_parsed_source.strip('\n')

        if not_parsed:
            code += '/*START not parsed (outside any class):\n \n'
            code += not_parsed + '\n' * 2
            code += 'END not parsed (outside any class)\n*/' + '\n' * 2
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
        pointer = ''
        or_objc_type = objc_type

        if '*' in objc_type:
            objc_type = re.sub(r'\*', '', objc_type).strip(' ')
            pointer = '*'

        if objc_type in self.equivalent_dict.keys():
            return self.equivalent_dict[objc_type] + pointer
        else:
            return or_objc_type

    def translate_method_name(self, class_name, method_name):

        #not using 'scene': 'create' because template alreade include that name
        translate_method_dict = ({'dealloc': '~' + class_name})

        if method_name in translate_method_dict.keys():
            return translate_method_dict[method_name]
        else:
            return method_name

    def translate_method_code(self, class_name, body):
        arg = '[_\w\d]*'
        first_parameter = '(?P<first_argument>:[_\w]+)?'
        args_group = '(?P<arguments>\ [\w_]+:[_\w\d+]*)*'
        method_name = '(?P<method_name>[_\w]+)'
        obj = '(?P<obj>[_\w]+)'
        object_ = '\[' + obj
        spaces = '(?P<space>\ *)'
        spaces2 = '(?P<space2>\ *)'
        message = object_ + '\ ' + method_name + first_parameter +\
                 args_group + '\];'

        eq = '\ *=\ *'
        set_arguments = '(?P<set_arguments>position|color|anchorPoint|' +\
                        'visible|sprite)'

        sett = '^' + spaces + obj + '.' + set_arguments + eq +\
                 '(?P<rvalue>.*?);$'

        assign = '^' + spaces + '(?:(?P<lval>' + arg + ')' + eq + ')' + message

        alloc_init = '^' + spaces + '(?:(?P<lval>' + arg + ')' + eq + ')' +\
                    '\[\[' + obj + '\ alloc\]\ init\];'

        rgx = re.compile(assign, re.MULTILINE)
        body = rgx.sub(self.translate_message, body)

        message = '^' + spaces2 + message

        rgx = re.compile(message, re.MULTILINE)
        body = rgx.sub(self.translate_message, body)

        rgx = re.compile(sett, re.MULTILINE | re.DOTALL)
        body = rgx.sub(self.translate_set, body)

        #FIXME: only reemplace in not commented lines
        for t in self.equivalent_dict.keys():
            body = re.sub(t, self.equivalent_dict[t], body)

        rgx = re.compile(alloc_init, re.MULTILINE)
        body = rgx.sub(self.translate_alloc_init, body)

        #TODO:
        #[_gameMenu runAction: [CCFadeOut actionWithDuration:CONTROLS_FADE_DURATION]]
        #_itemsLayer = [[LvkItemsLayer alloc] initWithLvkItems:items];
        #[_gameMenu runAction: [CCFadeOut actionWithDuration:CONTROLS_FADE_DURATION]];

        return body

    def translate_message(self, matchObj):
        m = matchObj
        arguments = m.group('arguments')

        space = m.groupdict().get('space')
        spaces = m.groupdict().get('space2')
        first_argument = m.groupdict().get('first_argument')
        larg = m.groupdict().get('lval')

        if not spaces:
            spaces = ''

        if not space:
            space = ''

        to_return = spaces + '// ' + m.group(0).strip(' ') + '\n' + spaces

        if larg:
            to_return += space + larg + ' = '

        if arguments:

            arguments = re.sub(r'\ *\w*\:([_\w\d+]*)',
                         lambda mm: mm.group(1) + ', ',
                         arguments).rstrip(', ')

            to_return += m.group('obj') + '->' + m.group('method_name') +\
              '(' + first_argument.lstrip(':') + ', ' +\
              arguments + ');'

        elif first_argument:
            to_return += m.group('obj') + '->' + m.group('method_name') +\
                     '(' + first_argument.lstrip(':') + ');'
        else:
            to_return += m.group('obj') + '->' + m.group('method_name') +\
                     '(' + ');'

        #remove self-> (coding style desition)
        to_return = to_return.replace('self->', '')

        return to_return

    def translate_set(self, matchObj):
        setmtd = matchObj.group('set_arguments')[0].upper() +\
                 matchObj.group('set_arguments')[1:]
        spaces = matchObj.group('space')
        method = 'set' + setmtd
        rslt = spaces + '//' + matchObj.group(0) + '\n' +\
             spaces + matchObj.group('obj') + '->' +\
             method + '(' + matchObj.group('rvalue') + ');'

        return rslt

    def translate_alloc_init(self, matchObj):
        space = matchObj.groupdict().get('space')
        lval = matchObj.group('lval')
        obj = matchObj.group('obj')
        rslt = space + '//' + matchObj.group(0) + '\n'
        rslt += space + lval + ' = new ' + obj + '();\n' + space + lval +\
                 '->init();'
        return rslt