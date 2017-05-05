# dblp_comp
Bibtex parser and auto-completer. Collects data from DBLP and updates your bib files.

This script parses a bib file, searches its title in DBLP, and writes the
data collected to another bib file. The reference ID is left unchanged so
there is no need to update the references.

All the data imported from DBLP will be added to the entry. However,
the user can create exceptions to ignore some of the imported data (-e).

Usage:
  python dblp_comp.py -i infile.bib -o outf.bib -e exception1 -e exception2

Help:
  python dblp_comp.py -h

