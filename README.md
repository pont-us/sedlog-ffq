# sedlog-ffq: an example graphic sediment log using Python

By Pontus Lurcock (pont -at- talvi -dot- net), 2009.

Warning: this is not a polished, general-purpose utility. It's a one-off
program written for a specific task. I'm releasing it in the hope that
parts of the code may be useful or informative for other developers.

## Rationale

For my PhD dissertation [1], I needed to produce a graphical sediment
log of a 25-metre section, integrating various sedimentological and
magnetic observations into a single stratigraphic column. I wrote a
script in Python 2 to do this. The script reads data from external text
files and from hard-coded structures within the code itself and uses
Cairo (via the PyCairo bindings) to produce a PDF from them.

As it stands, this is a one-shot single-purpose program rather than a
generally useful utility: the data for my specific section is not well
separated from the general-purpose plotting code, and there are a few
ad-hoc tweaks to improve the appearance of these particular data. The
code is sparsely commented and documented only by this README, but is
relatively clean and comprehensible. It may provide some useful examples
or fragments for anyone trying to achieve something similar. In
particular, the file `symb.py` contains Cairo implementations of a few
sedimentological pattern fills, which would be easy to reuse elsewhere.

[1] http://hdl.handle.net/10523/2281

## Requirements

First, ensure that the Nimbus Sans L Regular Condensed font is
installed. This font is provided in this repository in the file
`NimbusSanL-ReguCond.ttf`. On Ubuntu Linux, it can be installed by
copying the file to the `.fonts` subdirectory in the home directory,
and running `fc-cache`.

The program requires the Python bindings for the Cairo library. On
Ubuntu, these can be installed via the package `python-cairo` (which
will also install the cairo library itself as a dependency if required).

## Usage

Run the `make-log.py` script to generate a set of sediment log PDFs in
the `output` directory.

## Notes

The original program used a customized version of Jos Buivenga's
font Delicious. The font's license terms don't allow me to redistribute
it, so for this release I have replaced it with Nimbus Sans L Condensed,
which is included in this repository for convenience.

The ‘ffq’ in ‘sedlog-ffq’ is an abbreviation for ‘Fairfield Quarry’,
the location of the logged section.

## License

The code is released under the MIT license (see comments in Python
source files for exact license terms). The Nimbus Sans L Regular
Condensed font is redistributed under the terms of the GNU General
Public License, version 2 (full text at
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html )
