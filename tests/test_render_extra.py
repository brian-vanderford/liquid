"""Test cases for rendering non-standard "extra" tags."""
# pylint: disable=missing-function-docstring,too-many-public-methods,missing-class-docstring
import asyncio
import unittest
from typing import List

from liquid import golden
from liquid.environment import Environment
from liquid.exceptions import Error
from liquid.extra import register_inline_if_expressions
from liquid.extra import register_inline_if_expressions_with_parens
from liquid.extra import IfNotTag
from liquid.golden.case import Case
from liquid.loaders import DictLoader
from liquid.template import AwareBoundTemplate


class RenderExtraTagsTestCase(unittest.TestCase):
    """Test cases for non-standard tags."""

    # TODO: Split into multiple TestCase classes, one for each environment config

    def _test(self, test_cases: List[Case]) -> None:
        for case in test_cases:
            env = Environment(loader=DictLoader(case.partials))
            env.add_tag(IfNotTag)
            register_inline_if_expressions(env)
            env.template_class = AwareBoundTemplate

            with self.subTest(msg=case.description):
                if case.error:
                    with self.assertRaises(Error):
                        template = env.from_string(case.template, globals=case.globals)
                        result = template.render()
                else:
                    template = env.from_string(case.template, globals=case.globals)
                    result = template.render()
                    self.assertEqual(result, case.expect)

        async def coro(template: AwareBoundTemplate):
            return await template.render_async()

        for case in test_cases:
            env = Environment(loader=DictLoader(case.partials))
            env.add_tag(IfNotTag)
            register_inline_if_expressions(env)
            env.template_class = AwareBoundTemplate

            with self.subTest(msg=case.description, asynchronous=True):
                if case.error:
                    with self.assertRaises(Error):
                        template = env.from_string(case.template, globals=case.globals)
                        result = asyncio.run(coro(template))
                else:
                    template = env.from_string(case.template, globals=case.globals)
                    result = asyncio.run(coro(template))
                    self.assertEqual(result, case.expect)

    def test_render_standard_if_tag(self) -> None:
        """Test that the `if (not)` tag renders standard `if` tags."""
        self._test(golden.if_tag.cases)

    def test_render_non_standard_if_tag(self) -> None:
        """Test that we can render `if` tags with logical `not` and grouping
        with parentheses."""
        test_cases = [
            Case(
                description="not false",
                template=r"{% if not false %}foo{% endif %}",
                expect="foo",
            ),
            Case(
                description="not true",
                template=r"{% if not true %}foo{% endif %}",
                expect="",
            ),
            Case(
                description="literal boolean filter",
                template=r"{{ false | default: true }}",
                expect="true",
            ),
            Case(
                description="not comparison to empty",
                template=r"{% if not '' == empty %}foo{% endif %}",
                expect="",
            ),
            Case(
                description="not contains",
                template=r"{% if not foo contains 'z' %}bar{% endif %}",
                expect="bar",
                globals={"foo": ["a", "b", "c"]},
            ),
            Case(
                description="and not",
                template=r"{% if not foo and not bar %}hello{% endif %}",
                expect="hello",
                globals={"foo": False, "bar": False},
            ),
            Case(
                description="true and not",
                template=r"{% if foo and not bar %}hello{% endif %}",
                expect="hello",
                globals={"foo": True, "bar": False},
            ),
            Case(
                description="not equals",
                template=r"{% if not foo == True %}hello{% endif %}",
                expect="hello",
                globals={"foo": False},
            ),
            Case(
                description="not not equals False",
                template=r"{% if not foo != true %}hello{% endif %}",
                expect="",
                globals={"foo": False},
            ),
            Case(
                description="not not equals true",
                template=r"{% if not foo != true %}hello{% endif %}",
                expect="hello",
                globals={"foo": True},
            ),
            Case(
                description="not contains with parens",
                template=r"{% if not (foo contains 'z') %}bar{% endif %}",
                expect="bar",
                globals={"foo": ["a", "b", "c"]},
            ),
        ]
        self._test(test_cases)

    def test_render_inline_if_output_statement(self) -> None:
        """Test that we can render output statements with inline `if` expressions."""
        test_cases = [
            Case(
                description="string literal with true condition",
                template=r"{{ 'hello' if true }}",
                expect="hello",
                globals={},
                partials={},
            ),
            Case(
                description="default to undefined",
                template=r"{{ 'hello' if false }}",
                expect="",
                globals={},
                partials={},
            ),
            Case(
                description="early  filter",
                template=r"{{ 'hello' | upcase if true }}",
                expect="HELLO",
                globals={},
                partials={},
            ),
            Case(
                description="string literal with false condition and alternative",
                template=r"{{ 'hello' if false else 'goodbye' }}",
                expect="goodbye",
                globals={},
                partials={},
            ),
            Case(
                description="object and condition from context with tail filter",
                template=r"{{ greeting if settings.foo else 'bar' || upcase }}",
                expect="HELLO",
                globals={"settings": {"foo": True}, "greeting": "hello"},
                partials={},
            ),
        ]
        self._test(test_cases)

    def test_render_inline_if_assignment_tags(self) -> None:
        """Test that we can render `assign` tags with inline `if` expressions."""
        test_cases = [
            Case(
                description="string literal",
                template=r"{% assign foo = 'hello' %}{{ foo }}",
                expect="hello",
                globals={},
                partials={},
            ),
            Case(
                description="string literal with true condition",
                template=r"{% assign foo = 'hello' if true %}{{ foo }}",
                expect="hello",
                globals={},
                partials={},
            ),
            Case(
                description="default to undefined",
                template=r"{% assign foo = 'hello' if false %}{{ foo }}",
                expect="",
                globals={},
                partials={},
            ),
            Case(
                description="early  filter",
                template=r"{% assign foo = 'hello' | upcase if true %}{{ foo }}",
                expect="HELLO",
                globals={},
                partials={},
            ),
            Case(
                description="string literal with false condition and alternative",
                template=r"{% assign foo = 'hello' if false else 'goodbye' %}{{ foo }}",
                expect="goodbye",
                globals={},
                partials={},
            ),
            Case(
                description="object and condition from context with tail filter",
                template=(
                    r"{% assign foo = greeting if settings.foo else 'bar' || upcase %}"
                    r"{{ foo }}"
                ),
                expect="HELLO",
                globals={"settings": {"foo": True}, "greeting": "hello"},
                partials={},
            ),
        ]
        self._test(test_cases)

    def test_render_inline_if_echo_tags(self) -> None:
        """Test that we can render `echo` tags with inline `if` expressions."""
        test_cases = [
            Case(
                description="string literal",
                template=r"{% echo 'hello' %}",
                expect="hello",
                globals={},
                partials={},
            ),
            Case(
                description="string literal with true condition",
                template=r"{% echo 'hello' if true %}",
                expect="hello",
                globals={},
                partials={},
            ),
            Case(
                description="default to undefined",
                template=r"{% echo 'hello' if false %}",
                expect="",
                globals={},
                partials={},
            ),
            Case(
                description="early  filter",
                template=r"{% echo 'hello' | upcase if true %}",
                expect="HELLO",
                globals={},
                partials={},
            ),
            Case(
                description="string literal with false condition and alternative",
                template=r"{% echo 'hello' if false else 'goodbye' %}",
                expect="goodbye",
                globals={},
                partials={},
            ),
            Case(
                description="object and condition from context with tail filter",
                template=(r"{% echo greeting if settings.foo else 'bar' || upcase %}"),
                expect="HELLO",
                globals={"settings": {"foo": True}, "greeting": "hello"},
                partials={},
            ),
        ]
        self._test(test_cases)


# TODO: Test inline `if` tags with parens
