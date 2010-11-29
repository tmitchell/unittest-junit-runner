# Copyright (c) 2010, Mark Walling <mark@markwalling.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import unittest
import time

def split_test_name(test):
    name_parts = test.id().split('.')
    classname = '.'.join(name_parts[:-1])
    name = name_parts[-1]
    return classname, name

class JUnitTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(JUnitTest, self).__init__(*args, **kwargs)
        self.classname, self.name = split_test_name(self)


class JUnitTestSuite(unittest.TestSuite):
    def __init__(self, *args, **kwargs):
        super(JUnitTestSuite, self).__init__(*args, **kwargs)
        self.name = 'unittests'

class JUnitTestResult(unittest.TestResult):
    PASSED = 1
    FAILURE = 2
    ERROR = 3

    def __init__(self):
        super(JUnitTestResult, self).__init__() 
        self.all_tests = []
        self.test_times = {}
        self.test_status = {}
        self.test_traces = {}

    def startTest(self, test):
        self.all_tests.append(test)
        self.test_times[test] = time.time()
        super(JUnitTestResult, self).startTest(test)

    def stopTest(self, test):
        super(JUnitTestResult, self).stopTest(test)
        self.test_times[test] = time.time() - self.test_times[test]
    
    def prepare_for_print(self):
        for test, traceback in self.errors:
            self.test_status[test] = self.ERROR
            self.test_traces[test] = traceback
        for test, traceback in self.failures:
            self.test_status[test] = self.FAILURE
            self.test_traces[test] = traceback
        for test in self.all_tests:
            if not self.test_status.has_key(test):
                self.test_status[test] = self.PASSED
    
    def __repr__(self):
        return '<JUnitTestResult errors=%s failures=%s all_tests=%s test_times=%s test_status=%s>' % (
                self.errors, self.failures, self.all_tests, self.test_times, self.test_status)

class JUnitTestRunner:
    def __init__(self, filename):
        self.stream = open(filename, 'w')
        self.stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.stream.write('<testsuites>\n')

    def run(self, test):
        result = JUnitTestResult()
        start_time = time.time()
        test(result)
        stop_time = time.time()
        self.total_time = stop_time - start_time
        self.print_result(result, test.name)
        return result
    
    def print_result(self, result, name):
        result.prepare_for_print()
        
        stream = self.stream
        stream.write('<testsuite name="%(name)s" tests="%(total_tests)d" errors="%(test_errors)d" failures="%(test_failures)d" skip="0">\n' % {
            'name': name,
            'total_tests': result.testsRun,
            'test_errors': len(result.errors),
            'test_failures': len(result.failures),})
        for test in result.all_tests:
            test_time = result.test_times[test]
            stream.write('    <testcase classname="%(classname)s" name="%(name)s" time="%(time)d"' % {
                'classname': test.classname,
                'name': test.name,
                'time': test_time})
            if result.test_status[test] == JUnitTestResult.PASSED:
                stream.write(' />\n')
            else:
                if result.test_status[test] == JUnitTestResult.FAILURE:
                    tag_name = 'failure'
                    ex_type = 'exceptions.AssertionError'
                    ex_msg = ''
                elif result.test_status[test] == JUnitTestResult.ERROR:
                    tag_name = 'error'
                    ex_type, ex_msg = result.test_traces[test].splitlines()[-1].split(':', 2)
                    ex_type = 'exceptions.' + ex_type
                    ex_msg = ex_msg.strip()
                stream.write('>\n        <%(tag_name)s type="%(ex_type)s" message="%(ex_msg)s">\n<![CDATA[%(traceback)s]]>\n        </%(tag_name)s>\n    </testcase>\n' % {
                    'tag_name': tag_name,
                    'ex_type': ex_type,
                    'ex_msg': ex_msg,
                    'traceback': result.test_traces[test],})
        stream.write('</testsuite>\n')

    def __del__(self):
        self.stream.write('</testsuites>\n')