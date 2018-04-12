#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from glob import glob
from pyPdf import PdfFileReader, PdfFileWriter

def merge(path, blank_filename, output_filename):
    blank = PdfFileReader(file(blank_filename, "rb"))
    output = PdfFileWriter()

    for pdffile in glob('*.pdf'):
        if pdffile == output_filename:
            continue
        print("Parse '%s'" % pdffile)
        document = PdfFileReader(open(pdffile, 'rb'))
        for i in range(document.getNumPages()):
            output.addPage(document.getPage(i))

        if document.getNumPages() % 2 == 1:
            output.addPage(blank.getPage(0))
            print("Add blank page to '%s' (had %i pages)" % (pdffile, document.getNumPages()))
    print("Start writing '%s'" % output_filename)
    output_stream = file(output_filename, "wb")
    output.write(output_stream)
    output_stream.close()

if __name__ == "__main__":
    parser = ArgumentParser()

    # Add more options if you like
    parser.add_argument("-o", "--output", dest="output_filename", default="merged.pdf",
                      help="write merged PDF to FILE", metavar="FILE")
    parser.add_argument("-b", "--blank", dest="blank_filename", default="blank.pdf",
                      help="path to blank PDF file", metavar="FILE")
    parser.add_argument("-p", "--path", dest="path", default=".",
                      help="path of source PDF files")

    args = parser.parse_args()
    merge(args.path, args.blank_filename, args.output_filename)