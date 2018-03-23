# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2017 Science and Technology Facilities Council
#
# All rights reserved.
#
# Modifications made as part of the fparser project are distributed
# under the following license:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##############################################################################
# Modified M.Hambley, UK Met Office
##############################################################################
'''
Test battery associated with fparser.base_classes package.
'''
import re
import pytest
import fparser.base_classes
import fparser.parsefortran
import fparser.readfortran
import fparser.sourceinfo
import fparser.utils


def test_statement_logging(log, monkeypatch):
    '''
    Tests the Statement class' logging methods.
    '''
    reader = fparser.readfortran.FortranStringReader("dummy = 1")
    parser = fparser.parsefortran.FortranParser(reader)

    monkeypatch.setattr(fparser.base_classes.Statement,
                        'process_item', lambda x: None, raising=False)
    unit_under_test = fparser.base_classes.Statement(parser, None)

    unit_under_test.error('Scary biscuits')
    assert(log.messages == {'critical': [],
                            'debug':    [],
                            'error':    ['Scary biscuits'],
                            'info':     [],
                            'warning':  []})

    log.reset()
    unit_under_test.warning('Trepidacious Cetations')
    assert(log.messages == {'critical': [],
                            'debug':    [],
                            'error':    [],
                            'info':     [],
                            'warning':  ['Trepidacious Cetations']})

    log.reset()
    unit_under_test.info('Hilarious Ontologies')
    assert(log.messages == {'critical': [],
                            'debug':    [],
                            'error':    [],
                            'info':     ['Hilarious Ontologies'],
                            'warning':  []})


def test_log_comment_mix(log):
    '''
    Tests that unexpected Fortran 90 comment in fixed format source is logged.
    '''
    class EndDummy(fparser.base_classes.EndStatement):
        '''
        Dummy EndStatement.
        '''
        match = re.compile(r'\s*end(\s*thing\s*\w*|)\s*\Z', re.I).match

    class BeginHarness(fparser.base_classes.BeginStatement):
        '''
        Dummy BeginStatement.
        '''
        end_stmt_cls = EndDummy
        classes = []
        match = re.compile(r'\s*thing\s+(\w*)\s*\Z', re.I).match

        def get_classes(self):
            '''
            Returns an empty list of contained statements.
            '''
            return []

    code = '      x=1 ! Cheese'
    parent = fparser.readfortran.FortranStringReader(code)
    parent.set_format(fparser.sourceinfo.FortranFormat(False, True))
    item = fparser.readfortran.Line(code, (1, 1), None, None, parent)
    with pytest.raises(fparser.utils.AnalyzeError):
        __ = BeginHarness(parent, item)
    expected = '    1:      x=1 ! Cheese <== ' \
               + 'no parse pattern found for "x=1 ! cheese" ' \
               + "in 'BeginHarness' block, " \
               + 'trying to remove inline comment (not in Fortran 77).'
    result = log.messages['warning'][0].split('\n')[1]
    assert result == expected


def test_log_unexpected(log):
    '''
    Tests that an unexpected thing between begin and end statements logs an
    event.
    '''
    class EndThing(fparser.base_classes.EndStatement):
        '''
        Dummy EndStatement class.
        '''
        isvalid = True
        match = re.compile(r'\s*end(\s+thing(\s+\w+)?)?\s*$', re.I).match

    class BeginThing(fparser.base_classes.BeginStatement):
        '''
        Dummy BeginStatement class.
        '''
        end_stmt_cls = EndThing
        classes = []
        match = re.compile(r'\s*thing\s+(\w+)?\s*$', re.I).match

        def get_classes(self):
            '''
            Returns an empty list of contained classes.
            '''
            return []

    code = ['      jumper', '      end thing']
    parent = fparser.readfortran.FortranStringReader('\n'.join(code))
    parent.set_format(fparser.sourceinfo.FortranFormat(False, True))
    item = fparser.readfortran.Line(code[0], (1, 1), None, None, parent)
    with pytest.raises(fparser.utils.AnalyzeError):
        __ = BeginThing(parent, item)
    expected = '    1:      jumper <== no parse pattern found for "jumper" ' \
               "in 'BeginThing' block."
    result = log.messages['warning'][0].split('\n')[1]
    assert result == expected