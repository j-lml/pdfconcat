#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime, calendar
import glob
import os
import sys
import fnmatch
import ntpath
import urllib
import time
import logging

from shutil import copyfile
import shutil

from argparse import ArgumentParser
from glob import glob
from pyPdf import PdfFileReader, PdfFileWriter

from subprocess import call
import subprocess

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

def pdf_num_pages(pathfile):
    document = PdfFileReader(open(pathfile, 'rb'))
    return document.getNumPages()

def pdf_is_odd(pathfile):
    #es impar? si impar => poner pagina en blanco
    flag=False
    if ( pdf_num_pages(pathfile) % 2 == 1 ):
        flag=True
    return flag


#devuelve array de nombres de ficheros (incluido el PATH) de forma recursiva
#used: para buscar ficheros que ya existen
def get_files(dirname, ext):
    matches = []
    for root, dirnames, filenames in os.walk(dirname):
        for filename in fnmatch.filter(filenames, ext):
            matches.append(os.path.join(root, filename))
    return matches

#devuelve la hoja (nombre del fichero) de cierto PATH
def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

PATH_BASE='./pdf/'
OUTPUT='output.pdf'

def load_files(pathpdf):
    #obtiene todos los ficheros de cierto tipo de forma recursiva
    files= get_files(pathpdf, '*.pdf')
    files= [path_leaf(path) for path in files]

    return sorted(files)

def exec_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait();


def merge_files(files):
    for f in files:
        filepath=PATH_BASE + f


        #si no existe => crear el output con el fichero que corresponda
        if not os.path.isfile(OUTPUT):
            print('creando PDF: ' + f)
            copyfile(filepath, OUTPUT)
            continue

        #comprobar num de paginas
        fileout= OUTPUT
        num_pages=pdf_num_pages(fileout)
        add_pages=pdf_is_odd(fileout)

        #si es impar => concatener con pagina
        if add_pages == True:
            #pdftk.exe output.pdf blank.pdf cat output output2.pdf
            #pr=call(["pdftk.exe", OUTPUT, "blank.pdf", "cat", "output" , 'TMP_'+OUTPUT])

            command="pdftk.exe " + OUTPUT +" blank.pdf cat output TMP_" + OUTPUT
            exec_command(command)

            # os.system("pdftk.exe " + OUTPUT +" blank.pdf cat output TMP_" + OUTPUT)
            # os.close( 'TMP_'+OUTPUT )
            # os.close( OUTPUT )
            #os.rename('TMP_'+OUTPUT, OUTPUT)

            shutil.copy("TMP_" + OUTPUT, OUTPUT)
            os.remove("TMP_" + OUTPUT)

            print('+new blank page')

        #en cualquier caso => concatenar con el fichero
        #pr=call(["pdftk.exe", OUTPUT, fileout, "cat", "output" , 'TMP_'+OUTPUT])
        #pr.wait()
        # os.system("pdftk.exe " + OUTPUT +" "+fileout+ " cat output TMP_" + OUTPUT)
        # os.close( 'TMP_'+OUTPUT )
        # os.close( OUTPUT )

        command="pdftk.exe " + OUTPUT +" "+ fileout + " cat output TMP_" + OUTPUT
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait();

        #os.rename('TMP_'+OUTPUT, OUTPUT)
        # command="rename TMP_" + OUTPUT + " " + OUTPUT
        # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        # process.wait();

        shutil.copy("TMP_" + OUTPUT, OUTPUT)
        os.remove("TMP_" + OUTPUT)

        print('+'+f)

    print('end.')



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
    #merge(args.path, args.blank_filename, args.output_filename)
    files=load_files(PATH_BASE)
    print( repr(files) )
    merge_files(files)
