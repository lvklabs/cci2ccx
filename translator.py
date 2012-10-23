import re
from pprint import pprint
from collections import defaultdict
from string import Template


class CppTranslate(object):

    def __init__(self, parseObjc):
        self.data = parseObjc

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
        header += '/* not parsed \n -->'
        header += self.data.header.strip('\n') + '\n'
        header += '<-- not parsed */ \n'
        header += self.construct_clases_header()

        #header = self.add_macro_guard(header, filename)
        return header

    def construct_source(self):

        source = self.data.source_init_comment + '\n'
        source += self.data.source_include_block.replace(
                        "#import", "#include") + '\n' * 2
        source += self.data.source_defines + '\n' * 2
        source += '/* not parsed \n -->'
        source += self.data.source.strip('\n') + '\n'
        source += '<-- not parsed */' + '\n' * 2
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
        '''using the data from data.get_classes() create the string
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

        equivalent_dict = ({'YES': 'true', 'NO': 'false', 'BOOL': 'bool',
            'CGSize': 'CCSize', 'CGRect': 'CCRect', 'CGPoint': 'CCPoint',
            'CGFloat': 'CCFloat', 'NSString': 'CCString',
            'NSMutableDictionary': 'CCDictionary', 'NSDictionary': 'CCDictionary',
            'NSObject' : 'CCObject', 'NSInteger' : 'CCInteger', 'NSUInteger' : 'CCInteger'})

        if objc_type in equivalent_dict.keys():
            return equivalent_dict[objc_type]
        else:
            return objc_type
