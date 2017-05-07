###############################################################################
#   dblp_comp.py
#       mikel.fernandez@bsc.es
#
# This script parses a bib file, searches its title in DBLP, and writes the
# data collected to another bib file. The reference ID is left unchanged so
# there is no need to update the references.
#
# All the data imported from DBLP will be added to the entry. However,
# the user can create exceptions to ignore some of the imported data (-e).
#
# Usage:
#   python dblp_comp.py -i infile.bib -o outf.bib -e exception1 -e exception2
#
# Help:
#   python dblp_comp.py -h
###############################################################################

import getopt
from pylatexenc import latexencode
import re
import time
import xml.etree.ElementTree as ET
import urllib2
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *
from bibtexparser.bwriter import BibTexWriter
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# XML fields that we will ignore. ee, doi and author should be here, as they are parsed separately
# Other exceptions can be added with the -e parameters (see help)
exceptions = [ 'ee', 'doi', 'author' ] # do not modify 

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def pprint(color, head, title1, errortext = '', title2 = ''):
    if sys.stdout.isatty():
        if errortext == '':
            print color + bcolors.UNDERLINE + head + bcolors.ENDC + ': ' + title1 + ''
        elif title2 == '':
            print color + bcolors.UNDERLINE + head + bcolors.ENDC + ': ' + title1 + ' ' + bcolors.BOLD + '(' + errortext + ')' + bcolors.ENDC
        else:
            print color + bcolors.UNDERLINE + head + bcolors.ENDC + ': ' + title1 + ' ' + bcolors.UNDERLINE + 'vs' + bcolors.ENDC + ' ' + title2 + ' ' + bcolors.BOLD + '(' + errortext + ')' + bcolors.ENDC
    else:
        if errortext == '':
            print head + ': ' + title1
        elif title2 == '':
            print head + ': ' + title1 + ' (' + errortext + ')'
        else:
            print head + ': ' + title1 + ' vs ' + title2 + ' (' + errortext + ')'


def dblp_comp(inputfile, outputfile):
    # counters
    dblp_cnt = 0
    local_cnt = 0

    parser = BibTexParser()
    parser.customization = homogeneize_latex_encoding 
    with open(inputfile) as input_file:
        bib_database = bibtexparser.load(input_file, parser=parser)

    for entry in bib_database.entries:
        try:
            title = entry['title']
        except:
            pprint(bcolors.FAIL, 'LOCL', '(Unknown)', 'entry does not have a title')
            local_cnt += 1
            continue
        title = title.replace('}', '')
        title = title.replace('{', '')
        title = title.replace('\n', ' ')
        searchstr = re.sub(' ', '$.', title)
        searchstr = re.sub('$', '$', searchstr)
        try:
            xmlstr = urllib2.urlopen("http://dblp.org/search/publ/api/?q=" + searchstr + "&format=xml&h=1").read()
        except:
            pprint(bcolors.FAIL, 'LOCL', title, 'failed to fetch results from DBLP')
            local_cnt += 1
            continue
        xml = ET.fromstring(xmlstr)
        if xml.find('./hits').attrib['total'] != "0":
            hit = xml.find('./hits/hit/info/url')
            xmlstr = urllib2.urlopen(re.sub('/rec/', '/rec/xml/', hit.text)).read()
            xml = ET.fromstring(xmlstr)
            hit = xml.find('./')
            t =  re.sub('\.$', '', hit.find('title').text)
            t2 = t
            t2 = t2.replace('}', '')
            t2 = t2.replace('{', '')
            if t2.lower() == title.lower():
                #we found the same title; add the information on DBLP
                pprint(bcolors.OKGREEN, 'DBLP', t)
                dblp_cnt += 1
                entrytype = entry['ENTRYTYPE']
                entryid = entry['ID']
                entry.clear()
                entry['ENTRYTYPE'] = entrytype
                entry['ID'] = entryid
                # Title. Use t2 if you wish a title without brackets
                entry['title'] = latexencode.utf8tolatex(t)
                # Authors
                alist = ''
                first = True 
                for a in hit.findall('author'):
                    if not first:
                        alist +=" and "
                    first = False
                    alist += a.text
                entry['author'] = latexencode.utf8tolatex(alist)
                # DOI
                try:
                    doi = hit.find('ee').text.split('/')[3] + '/' + hit.find('ee').text.split('/')[4]
                    entry['doi'] = latexencode.utf8tolatex(doi)
                except:
                    pass
                # Other fields
                for i in hit:
                    if i.tag not in exceptions: 
                        entry[i.tag] = latexencode.utf8tolatex(i.text)
            else:
        	# if we don't find results, we keep our old data
                pprint(bcolors.WARNING, 'LOCL', t2, 'titles do not match', title)
                local_cnt += 1
        else:
            pprint(bcolors.WARNING, 'LOCL', title, 'entry not found')
            local_cnt += 1

        # As recommended by DBLP, sleep before continuing the search
        time.sleep(1)

    # write entries to output
    writer = BibTexWriter()
    writer.indent = '  '
    with open(outputfile, 'w') as output_file:
        bibtexparser.dump(bib_database, output_file)

    print ''
    if sys.stdout.isatty():
    	print 'Database updated. ' + bcolors.OKGREEN + str(dblp_cnt) + bcolors.ENDC + ' entries updated from DBLP, ' + bcolors.WARNING + str(local_cnt) + bcolors.ENDC + ' entries kept as they were.'
    else:
    	print 'Database updated. ' + str(dblp_cnt) + ' entries updated from DBLP, ' + str(local_cnt) + ' entries kept as they were.'
    print ''

def main(argv):
    inputfile = ''
    outputfile = ''
    extra_exceptions = [ ]
    try:
        opts, args = getopt.getopt(argv,"hi:o:e:")
    except getopt.GetoptError:
        print 'python dblp_comp.py -i <inputfile> -o <outputfile> [-e <field_to_exclude> -e <field_to_exclude2> ...]'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print 'python dblp_comp.py -i <inputfile> -o <outputfile> [-e <field_to_exclude> -e <field_to_exclude2> ...]'
            sys.exit()
        elif opt == "-i":
            inputfile = arg
        elif opt == "-o":
            outputfile = arg
        elif opt == "-e":
            extra_exceptions.append(arg)
            exceptions.append(arg)
    if inputfile == '':
        raise Exception("Input file must be defined")
    if outputfile == '':
        raise Exception("Output file must be defined")
    if len(extra_exceptions) > 0:
        print ''
        print "Omitting the following fields: " + str(extra_exceptions)
        print ''
    dblp_comp(inputfile, outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])
