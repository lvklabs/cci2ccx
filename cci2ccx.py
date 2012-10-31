#!/usr/bin/env python

#import optparse
import argparse
from parseObjc import ParseObjc
from translator import CppTranslate


def write_file(filename, content):
    f = open(filename, 'w')
    f.write(content)
    f.close()


def read_file(filepath):
    f = open(filepath, 'r')
    content = f.read()
    f.close()
    return content

if __name__ == '__main__':
    #opt_parser = optparse.OptionParser()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-hh", "--header", dest="header",
        help="header file")
    arg_parser.add_argument("-src", "--source", dest="source",
        help="source file, must provide one")
    arg_parser.add_argument("-o", "--path", dest="opath",
        help="TODO: Path to output files")

    args = arg_parser.parse_args()

    #if not args.source:
        #exit("not source indicated, \n please use -h to more help")

    #options = vars(options)

    source_file = args.source
    source = read_file(source_file)

    header_file = args.header
    header = read_file(header_file)

    parserObjc = ParseObjc()
    parserObjc.parse_source(source)
    parserObjc.parse_header(header)
    #parserObjc.list_clases_names()
    ptc = CppTranslate(parserObjc)
    header = ptc.construct_header()
    source = ptc.construct_source()

#Just for testing right now
    write_file(source_file + 'translated.cpp', source)
    write_file(header_file + 'translated.h', header)

'''
To test try to run this code :

python cci2ccx.py --source examples/EndLevelScene.m \
--header examples/EndLevelScene.h

'''
