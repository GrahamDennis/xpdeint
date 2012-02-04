#!/usr/bin/env python
# encoding: utf-8
"""
CodeParser.py

Created by Graham Dennis on 2009-06-27.

Copyright (c) 2009-2012, Graham Dennis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


The purpose of this module is to facilitate better understanding of user
code blocks by breaking the code up into Tokens (strings of text with an
associated meaning) and using this as the basis for all code modification.
We need to modify user code in a number of situations, the most obvious being
IP and EX operators where an expression like 'L[u]' in 'du_dt = L[u];' must be 
found and replaced with some other string. The trouble with using regular
expressions is that they would also match inside comments, string constants,
and so giving the user different results to what they were expecting.
"""

from pyparsing import \
        Word, alphas, alphanums, Regex, cppStyleComment, quotedString, Forward, \
        nestedExpr, OneOrMore, Suppress, oneOf, Keyword, Dict, Group, ZeroOrMore, \
        delimitedList, originalTextFor, Empty, opAssoc, \
        ParserElement, Optional, lineno, col, MatchFirst, Literal

ParserElement.enablePackrat()

import unittest

from xpdeint.ParserException import ParserException, parserWarning

class CodeParserException(ParserException):
    """
    A class for exceptions thrown by the C++ code parser.
    This class determines the line in the original script that
    corresponds to the part of the code block that triggered the
    exception.
    """
    def __init__(self, codeBlock, codeIndex, msg):
        ParserException.__init__(self, codeBlock.xmlElement, msg)
        
        self.columnNumber = col(codeIndex, codeBlock.codeString)
        self.lineNumber = codeBlock.scriptLineNumber + lineno(codeIndex, codeBlock.codeString)-1
    


identifier = Word(alphas + '_', alphanums + '_')
numericConstant = Regex(r'\b((0(x|X)[0-9a-fA-F]*)|(([0-9]+\.?[0-9]*)|(\.[0-9]+))((e|E)(\+|-)?[0-9]+)?)(L|l|UL|ul|u|U|F|f|ll|LL|ull|ULL)?\b')

ignoreExpr = cppStyleComment.copy() | quotedString.copy()

baseExpr = Forward()

arrayAccess = originalTextFor(nestedExpr('[', ']', baseExpr, ignoreExpr))
parenthisedExpression = originalTextFor(nestedExpr('(', ')', baseExpr, ignoreExpr))
functionCall = nestedExpr('(', ')', delimitedList(baseExpr), ignoreExpr)
alphaNumPlusSafePunctuation = alphanums + '!#$%&\\*+-./:;<=>@^_`{|}~'

baseExpr << OneOrMore(originalTextFor(identifier + functionCall) | quotedString.copy() \
                | identifier | numericConstant | arrayAccess | parenthisedExpression \
                | Word(alphaNumPlusSafePunctuation))
baseExpr.ignore(cppStyleComment.copy())


def targetComponentsForOperatorsInString(operatorNames, codeBlock):
    """
    Return a list of pairs of operator names and their targets that are in `codeString`.
    The valid operator names searched for are `operatorNames`. For example, if 'L' is in `operatorNames`,
    then in the code ``L[phi]`` the return value would be ``('L', 'phi', slice(firstCharacterIndex, lastCharacterIndex))``.
    """
    parser = MatchFirst(Keyword(operatorName) for operatorName in operatorNames).setResultsName('name') \
                + Optional(nestedExpr('[', ']', baseExpr, ignoreExpr).setResultsName('target'))
    parser.ignore(cppStyleComment.copy())
    parser.ignore(quotedString.copy())
    results = []
    for tokens, start, end in parser.scanString(codeBlock.codeString):
        if 'target' in tokens:
            results.append((tokens.name, ''.join(tokens.target.asList()[0]), slice(start, end)))
        else:
            raise CodeParserException(codeBlock, start, "Invalid use of '%s' operator in code block." % tokens.name)
    return results

def sliceFor(expr):
    """
    Helper to add a slice object to the ParseResults with name 'slice' which is the
    slice of the original string that these results correspond to.
    """
    locMarker = Empty().setParseAction(lambda s, loc, t: loc)
    matchExpr = locMarker("_original_start") + expr + locMarker("_original_end")
    def makeSlice(s, l, t):
        t["slice"] = slice(t["_original_start"], t["_original_end"])
        # Clean up the loc markers added above
        del t[0]
        del t[-1]
        del t["_original_start"]
        del t["_original_end"]
    matchExpr.setParseAction(makeSlice)
    return matchExpr

def nonlocalDimensionAccessForVectors(vectors, codeBlock):
    """
    Find all places in the `codeBlock` where any components of any of the `vectors`
    are accessed non-locally (usually by integer-valued dimensions) and return a ``(componentName, vector, resultDict, codeSlice)``
    tuple for each such occurrence. ``codeSlice`` is the character range over which this expression occurs,
    and ``resultDict`` is a dictionary describing how each dimension is accessed. See `nonlocalDimensionAccessForField`
    for more information about ``resultDict``.
    """
    componentNameToVectorMap = {}
    for v in vectors:
        componentNameToVectorMap.update(dict.fromkeys(v.components, v))
    result = nonlocalDimensionAccessForComponents(componentNameToVectorMap.keys(), codeBlock)
    return [(componentName, componentNameToVectorMap[componentName], resultDict, codeSlice) \
                for componentName, resultDict, codeSlice in result]

def nonlocalDimensionAccessForComponents(components, codeBlock):
    """
    Find all places in the `codeBlock` where any of `components` are accessed with
    non-locally (usually integer-valued dimensions) and return a ``(componentName, resultDict, codeSlice)``
    tuple for each such occurrence. The companion of `nonlocalDimensionAccessForVectors` and
    to be used when `components` are components of vectors.
    """
    dictionaryElement = identifier + Suppress('=>') + sliceFor(Group(baseExpr))
    nonlocalAccessDictParser = Dict(
        ZeroOrMore(Group(dictionaryElement + Suppress(','))) + Group(dictionaryElement)
    )
    parser = MatchFirst(Keyword(componentName) for componentName in components).setResultsName('name') \
                + nestedExpr('(', ')', nonlocalAccessDictParser, ignoreExpr).setResultsName('access')
    parser.ignore(cppStyleComment.copy())
    parser.ignore(quotedString.copy())
    results = []
    for tokens, start, end in parser.scanString(codeBlock.codeString):
        accessDict = {}
        tokenDict = tokens.access[0].asDict()
        for key, value in tokenDict.items():
            accessDict[key] = (' '.join(value[0].asList()), value.slice.start)
        results.append((tokens.name, accessDict, slice(start, end)))
    return results

def checkForIntegerDivision(codeBlock):
    """
    Raise a CodeParserException if the code contains what looks like an integer division.
    i.e. ``9/2`` or the like. This is because the user is likely to get unexpected results.
    The most notorious example of this is ``1/2`` which evaluates to zero.
    """
    parser = numericConstant.setResultsName('numerator') + '/' + numericConstant.setResultsName('denominator')
    parser.ignore(cppStyleComment.copy())
    parser.ignore(quotedString.copy())
    for tokens, start, end in parser.scanString(codeBlock.codeString):
        if tokens.numerator.isdigit() and tokens.denominator.isdigit():
            raise CodeParserException(
                codeBlock, start,
                "It looks like you are trying to divide two integers.\n"
                "One of the oddities of the C language is that the result of such an expression\n"
                "is the floor of that division instead of the real value.\n"
                "For example '1/2' would give '0' instead of '0.5'.\n"
                "The way to fix this is to turn one or both of the integers into real numbers\n"
                "by adding a decimal point. For example, '1/2' should be written as '1.0/2.0'.\n\n"
                "If you feel this warning is given in error, send an email to xmds-devel@lists.sourceforge.net"
            )
    

# The following code is stolen from pyparsing with optimisations made for our case.
def operatorPrecedence( baseExpr, opList ):
    """Helper method for constructing grammars of expressions made up of
       operators working in a precedence hierarchy.  Operators may be unary or
       binary, left- or right-associative.  Parse actions can also be attached
       to operator expressions.
       
       Parameters:
        - baseExpr - expression representing the most basic element for the nested
        - opList - list of tuples, one for each operator precedence level in the
          expression grammar; each tuple is of the form
          (opExpr, numTerms, rightLeftAssoc, parseAction), where:
           - opExpr is the pyparsing expression for the operator;
              may also be a string, which will be converted to a Literal;
              if numTerms is 3, opExpr is a tuple of two expressions, for the
              two operators separating the 3 terms
           - numTerms is the number of terms for this operator (must
              be 1, 2, or 3)
           - rightLeftAssoc is the indicator whether the operator is
              right or left associative, using the pyparsing-defined
              constants opAssoc.RIGHT and opAssoc.LEFT.
           - parseAction is the parse action to be associated with
              expressions matching this operator expression (the
              parse action tuple member may be omitted)
    """
    ret = Forward()
    lastExpr = baseExpr | ( Suppress('(') + ret + Suppress(')') )
    for i,operDef in enumerate(opList):
        opExpr,arity,rightLeftAssoc,pa = (operDef + (None,))[:4]
        if arity == 3:
            if opExpr is None or len(opExpr) != 2:
                raise ValueError("if numterms=3, opExpr must be a tuple or list of two expressions")
            opExpr1, opExpr2 = opExpr
        thisExpr = Forward()#.setName("expr%d" % i)
        if rightLeftAssoc == opAssoc.LEFT:
            if arity == 1:
                matchExpr = Group( lastExpr + OneOrMore( opExpr ) )
            elif arity == 2:
                if opExpr is not None:
                    matchExpr = Group( lastExpr + OneOrMore( opExpr + lastExpr ) )
                else:
                    matchExpr = Group( lastExpr + OneOrMore(lastExpr) )
            elif arity == 3:
                matchExpr = Group( lastExpr + opExpr1 + lastExpr + opExpr2 + lastExpr )
            else:
                raise ValueError("operator must be unary (1), binary (2), or ternary (3)")
        elif rightLeftAssoc == opAssoc.RIGHT:
            if arity == 1:
                matchExpr = Group( OneOrMore(opExpr) + thisExpr )
            elif arity == 2:
                if opExpr is not None:
                    matchExpr = Group( lastExpr + OneOrMore( opExpr + thisExpr ) )
                else:
                    matchExpr = Group( lastExpr + OneOrMore( thisExpr ) )
            elif arity == 3:
                matchExpr = Group( lastExpr + opExpr1 + thisExpr + opExpr2 + thisExpr )
            else:
                raise ValueError("operator must be unary (1), binary (2), or ternary (3)")
        else:
            raise ValueError("operator must indicate right or left associativity")
        if pa:
            matchExpr.setParseAction( pa )
        thisExpr << ( matchExpr | lastExpr )
        lastExpr = thisExpr
    ret << lastExpr
    return ret

def performIPOperatorSanityCheck(componentName, propagationDimension, operatorCodeSlice, codeBlock):
    """
    Check that the user hasn't tried to use an IP operator where an IP operator cannot be used.
    
    IP operators must be diagonal, so one cannot have expressions of the form ``dy_dt = L[x];`` for IP operators.
    This is valid for EX operators, but not for IP. This is a common mistake for users to make, and so we should
    do our best to spot it and report the error. Another mistake users make is trying to multiply the operator,
    for example ``dy_dt = i*L[y];``. This code does a sophisticated validation by constructing a parse tree for
    each statement in the code taking into account operator precedence. This sanity checking is even able to pick
    up problems such as ``dphi_dt = i*(V*phi + U*mod2(phi)*phi + T[phi]);``.
    If the user's code passes this test, then it is a reasonable assumption that they are using IP operators safely.
    """
    
    operatorString = codeBlock.codeString[operatorCodeSlice]
    
    expr = Forward()
    
    operatorKeyword = Keyword(operatorString).setResultsName('targetOperator')
    
    operand = operatorKeyword \
                | (identifier + Group('(' + delimitedList(expr) + ')')) \
                | (identifier + Group(OneOrMore('[' + expr + ']'))) \
                | quotedString.copy() \
                | identifier \
                | numericConstant
    operand.ignore(cppStyleComment.copy())
    
    expr << operatorPrecedence(
        operand,
        [
            (oneOf('++ --'), 1, opAssoc.LEFT),
            (oneOf('. ->'), 2, opAssoc.LEFT),
            (~oneOf('-> -= += *= &= |=') + oneOf('+ - ! ~ * & ++ --'), 1, opAssoc.RIGHT),
            (~oneOf('*= /= %=') + oneOf('* / %'), 2, opAssoc.LEFT),
            (~oneOf('++ -- -> -= +=') + oneOf('+ -'), 2, opAssoc.LEFT),
# Although the operators below don't all have the same precedence, as we don't actually
# care about them as they are all invalid uses of the IP operator, we can cheat and lump
# them together
            (~oneOf('<<= >>= &= |=') + oneOf('<< >> < <= > >= == != & ^ | && ||'), 2, opAssoc.LEFT),
# Correct ordering
            # (~oneOf('<<= >>=') + oneOf('<< >>'), 2, opAssoc.LEFT),
            # (~oneOf('<< >> <<= >>=') + oneOf('< <= > >='), 2, opAssoc.LEFT),
            # (oneOf('== !='), 2, opAssoc.LEFT),
            # (~oneOf('&& &=') + '&', 2, opAssoc.LEFT),
            # ('^', 2, opAssoc.LEFT),
            # (~oneOf('|| |=') + '|', 2, opAssoc.LEFT),
            # ('&&', 2, opAssoc.LEFT),
            # ('||', 2, opAssoc.LEFT),
            (('?',':'), 3, opAssoc.RIGHT),
            (~Literal('==') + oneOf('= += -= *= /= %= <<= >>= &= ^= |= =>'), 2, opAssoc.RIGHT),
            (',', 2, opAssoc.LEFT),
        ]
    )
    expr.ignore(cppStyleComment.copy())
    
    statement = expr + Suppress(';')
    
    stack = []
    expectedAssignmentVariable = 'd%(componentName)s_d%(propagationDimension)s' % locals()
    
    def validateStack():
        """
        It is the job of this function to validate the operations that the located operator is involved in.
        The stack describes the part of the parse tree in which the operator was found. The first element in the stack
        is the outermost operation, and the last the innermost. The last element is guaranteed to be the operator itself.
        """
        # Reverse the stack as we want to search the parse tree from inner-most expression to outer-most.
        stack.reverse()
        assignmentHit = False
        errorMessageCommon = "Due to the way IP operators work, they can only contribute to the derivative of the variable " \
            "they act on, i.e. dx_dt = L[x]; not dy_dt = L[x];\n\n"
        
        # We don't need to check the first element of the stack
        # as we are guaranteed that it is the operator itself. This will be useful for determining
        # which part of the parse tree we should be looking at.
        for idx, node in enumerate(stack[1:]):
            if len(node) == 1: continue
            # idx is the index in the stack of the next element *deeper* in the parse tree.
            previousStackEntry = stack[idx]
            if not isinstance(stack[idx], basestring):
                previousStackEntry = previousStackEntry.asList()
            binaryOpIdx = node.asList().index(previousStackEntry) - 1
            if binaryOpIdx < 0: binaryOpIdx = 1
            # Unary '+' is safe.
            if node[0] == '+': continue
            # Binary '+' is safe.
            if node[binaryOpIdx] == '+': continue
            # Binary '-' is safe if the operator is the first argument.
            if node[binaryOpIdx] == '-' and node.asList().index(previousStackEntry) == 0: continue
            # Assignment is safe if it there is only one, and if it's to the right variable
            if node[binaryOpIdx] in ['=', '+=']:
                if node[0] == expectedAssignmentVariable:
                    assignmentHit = True
                    continue
                else:
                    return errorMessageCommon + "In this case, you should probably use an EX operator instead of an "\
                            "IP operator."
            else:
                return errorMessageCommon + "You appear to be using the IP operator in an unsafe operation. " \
                        "The most likely cause is trying to multiply it by something, e.g. dphi_dt = 0.5*L[phi]; "\
                        "If this is the cause and you are multiplying by a constant, just move the constant into the "\
                        "definition of the operator itself. i.e. L = -0.5*kx*kx; If you are multiplying by something "\
                        "that isn't constant e.g. dphi_dt = x*L[phi]; where x is a dimension, you must use an EX operator "\
                        "instead."
        if not assignmentHit:
            return errorMessageCommon + "You appear to be missing the assignment for this particular operator."
        return True
    
    class FoundTargetException(Exception): pass
    
    def findOperatorInParseTree(results):
        stack.append(results)
        if 'targetOperator' in results:
            stack.append(results.targetOperator)
            raise FoundTargetException()
        for item in results:
            if isinstance(item, basestring): continue
            findOperatorInParseTree(item)
        del stack[-1]
    
    try:
        foundOperator = False
        for tokens, start, end in statement.scanString(codeBlock.codeString):
            if start > operatorCodeSlice.stop or end < operatorCodeSlice.start: continue
            try:
                findOperatorInParseTree(tokens)
            except FoundTargetException:
                foundOperator = True
                result = validateStack()
                if result is not True:
                    raise CodeParserException(
                        codeBlock,
                        operatorCodeSlice.start,
                        result + ("\n\nThe conflict was caused by the operator '%s'." \
                        % operatorString)
                    )
        if not foundOperator:
            parserWarning(
                codeBlock.xmlElement,
                "Unable to check the safety of your IP operator '%s' because the containing expression could not be found. "
                "Please send a copy of your script to xmds-devel@lists.sourceforge.net so this problem can be investigated." \
                % operatorString
            )
    except RuntimeError:
        parserWarning(
            codeBlock.xmlElement,
            "Unable to check the safety of your IP operator because your code is too deeply nested."
        )
    

# Below are a bunch of unit tests for the pyparsing-based code parser. These tests can be executed by
# directly executing this file, or by running the xpdeint test suite from 'run_tests.py'

class AbstractCodeParserTests(unittest.TestCase):
    @staticmethod
    def _block(codeString):
        class _Mock(object): pass
        block = _Mock()
        block.xmlElement = None
        block.scriptLineNumber = 1
        block.codeString = codeString
        return block
    

class TargetComponentsForOperatorsInStringTests(AbstractCodeParserTests):
    def test_combined(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(
                ['L', 'T'],
                self._block('/* L[phi] */ K[S] T[mu /* */] L[ j[0] + k] " T[ foo ]"')
            ),
            [('T', 'mu', slice(18, 29)), ('L', 'j[0]+k', slice(30, 42))]
        )
    def test_ignoreChildComment(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['T'], self._block('T[mu /* */ ]')),
            [('T', 'mu', slice(0, 12))]
        )
    def test_ignoreSiblingComment(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['Ky'], self._block('/* stuff */ Ky[ target]')),
            [('Ky', 'target', slice(12, 23))]
        )
    def test_ignoreSiblingQuotedString(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['F'], self._block('printf("F[psi * 0.98]"); F[phi];')),
            [('F', 'phi', slice(25, 31))]
        )
    def test_nestedOperators(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['Q'], self._block('Q[ Q[ phi]]')),
            [('Q', 'Q[ phi]', slice(0, 11))]
        )
    def test_unbalancedString(self):
        self.assertRaises(
            CodeParserException,
            targetComponentsForOperatorsInString, ['Txx'], self._block('Txx [ ( ]')
        )
    def test_withPrintf(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['L'],
                self._block('printf("L[psi]: %e\\n", L[psi]);')
            ),
            [('L', 'psi', slice(23, 29))]
        )
    def test_notGreedy(self):
        self.assertEqual(
            targetComponentsForOperatorsInString(['L'], self._block('notL[phi];')),
            []
        )
    def test_invalidSyntax(self):
        self.assertRaises(
            CodeParserException,
            targetComponentsForOperatorsInString, ['L'], self._block('L * 5')
        )
    

class NonlocalDimensionAccessForComponentsTests(AbstractCodeParserTests):
    def test_combined(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(
                ['phi'],
                self._block("phi(j => 0 - 9 /* ignore me */, kz => -kz)")
            ),
            [('phi', {'j': ('0 - 9', 9), 'kz': ('-kz', 38)}, slice(0, 42))]
        )
    def test_multipleAccess(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(
                ['velocity'], 
                self._block("stuff whatever velocity(time => 0.3e-6, idx => -9 * (1 + 2))")
            ),
            [('velocity', {'time': ('0.3e-6', 32), 'idx': ('-9 * (1 + 2)', 47)}, slice(15, 60))]
        )
    def test_basic(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(['u'], self._block("u(p => q)")),
            [('u', {'p': ('q', 7)}, slice(0, 9))]
        )
    def test_accessMultipleTimes(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(
                ['foo'],
                self._block("foo(uv => uk * 2) + foo(mb => uv)")
            ),
            [('foo', {'uv': ('uk * 2', 10)}, slice(0, 17)),
             ('foo', {'mb': ('uv', 30)}, slice(20, 33))]
        )
    def test_accessDifferentVariables(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(
                ['foo', 'bar'],
                self._block("bar(bang => bam) / foo( someDim => 7 + exp(-2.0))")
            ),
            [('bar', {'bang': ('bam', 12)}, slice(0, 16)),
             ('foo', {'someDim': ('7 + exp(-2.0)', 35)}, slice(19, 49))]
        )
    def test_withPrintf(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(
                ['psi'],
                self._block('printf("psi(j => 8): %e\\n", psi(j => 8));')
            ),
            [('psi', {'j': ('8', 37)}, slice(28, 39))]
        )
    def test_notGreedy(self):
        self.assertEqual(
            nonlocalDimensionAccessForComponents(['psi'], self._block('notpsi(dim => value)')),
            []
        )

class IntegerDivisionTests(AbstractCodeParserTests):
    def test_floatDivision(self):
        self.assertEqual(
            checkForIntegerDivision(self._block('1.0 / 5.0')),
            None
        )
    def test_symbolDivision(self):
        self.assertEqual(
            checkForIntegerDivision(self._block(' M_PI / a')),
            None
        )
    def test_integerDivisionByDouble(self):
        self.assertEqual(
            checkForIntegerDivision(self._block(' 1 / 2.0')),
            None
        )
    def test_doubleDivisionByInteger(self):
        self.assertEqual(
            checkForIntegerDivision(self._block(' 1.0 / 9')),
            None
        )
    def test_integerDivision(self):
        self.assertRaises(
            CodeParserException,
            checkForIntegerDivision, self._block(' 135 / 9')
        )
    def test_ignoreComments(self):
        self.assertEqual(
            checkForIntegerDivision(self._block(' /* 1 / 56 */')),
            None
        )
    def test_ignoreStrings(self):
        self.assertEqual(
            checkForIntegerDivision(self._block('printf("567 / 962")')),
            None
        )

class IPOperatorSanityCheckTests(AbstractCodeParserTests):
    def test_combined(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'phi', 't', slice(12, 18),
            self._block("dphi_dt = 1-L[phi]; a = b;")
        )
    def test_basic(self):
        self.assertEqual(
            performIPOperatorSanityCheck(
                'psi', 'z', slice(10, 16),
                self._block('dpsi_dz = T[psi];')
            ),
            None
        )
    def test_assignmentToIncorrectVariable(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'y', 't', slice(8, 13),
            self._block("dx_dt = Kt[y];")
        )
    def test_unsafeUnaryOperation(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'y', 't', slice(9, 13),
            self._block("dy_dt = -K[y];")
        )
    def test_unsafeBinaryOperation(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'y', 'x', slice(8, 13),
            self._block("dy_dx = Z[y] / 9.0;")
        )
    def test_safeBinaryOperation(self):
        self.assertEqual(
            performIPOperatorSanityCheck('x', 'z', slice(14, 18),
                self._block("dx_dz = 6.0 + W[x];")
            ),
            None
        )
    def test_safeSubtraction(self):
        self.assertEqual(
            performIPOperatorSanityCheck('x', 'z', slice(8, 13),
                self._block("dx_dz = W[x] - phi;")
            ),
            None
        )
    def test_unsafeSubtraction(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'var', 'time', slice(19, 27),
            self._block("dvar_dtime = 1.0 - Foo[var];")
        )
    def test_hiddenUnsafeOperation(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'foo', 't', slice(30, 36),
            self._block("dfoo_dt = i * (fine + dandy + K[foo] );")
        )
    def test_complicatedSafeOperation(self):
        self.assertEqual(
            performIPOperatorSanityCheck('bar', 'baz', slice(43, 50),
                self._block("dbar_dbaz = 9.0 * 7 + (something - other + GH[bar]);")
            ),
            None
        )
    def test_missingAssignment(self):
        self.assertRaises(
            CodeParserException,
            performIPOperatorSanityCheck,
            'foo', 't', slice(0, 6),
            self._block("T[foo];")
        )
    def test_realExample(self):
        self.assertEqual(
            performIPOperatorSanityCheck('phi1', 't', slice(11, 18),
                self._block('dphi1_dt = T[phi1] - 1.0/hbar*(V + Uint*((phi1) + (phi0)) - eta*mu)*phi1;')
            ),
            None
        )


if __name__ == '__main__':
    unittest.main()

