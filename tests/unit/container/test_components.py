from typing import Annotated

import pytest

from dishka import (
    Component,
    FromComponent,
    Provider,
    Scope,
    alias,
    make_async_container,
    make_container,
    provide,
)
from dishka.exceptions import NoFactoryError


class MainProvider(Provider):
    scope = Scope.APP

    def __init__(self, value: int, component: Component | None = None):
        super().__init__(component=component)
        self.value = value

    @provide
    def foo(self, a: Annotated[float, FromComponent("X")]) -> complex:
        return a * 10

    @provide
    def bar(self) -> int:
        return self.value


class AliasedProvider(Provider):
    scope = Scope.APP

    float_alias = alias(source=float, component="X")

    @provide
    def foo(self, a: float) -> complex:
        return a * 10

    @provide
    def bar(self) -> int:
        return 20


class XProvider(Provider):
    scope = Scope.APP
    component = "X"

    @provide
    def foo(self, a: Annotated[int, FromComponent()]) -> float:
        return a + 1


def test_from_component():
    container = make_container(MainProvider(20), XProvider())
    assert container.get(complex) == 210
    assert container.get(float, component="X") == 21
    with pytest.raises(NoFactoryError):
        container.get(float)


@pytest.mark.asyncio()
async def test_from_component_async():
    container = make_async_container(MainProvider(20), XProvider())
    assert await container.get(complex) == 210
    assert await container.get(float, component="X") == 21
    with pytest.raises(NoFactoryError):
        await container.get(float)


def test_change_component():
    container = make_container(MainProvider(20).to_component("Y"))
    assert container.get(int, component="Y") == 20


def test_set_component():
    container = make_container(MainProvider(20, component="Y"))
    assert container.get(int, component="Y") == 20


def test_from_component_alias():
    container = make_container(AliasedProvider(), XProvider())
    assert container.get(complex) == 210
    assert container.get(float, component="X") == 21
    assert container.get(float) == 21


class Provider1(Provider):
    scope = Scope.APP
    component = "1"

    @provide
    def foo(self) -> int:
        return 1

    @provide
    def bar(self, a: int) -> float:
        return a


class Provider2(Provider):
    scope = Scope.APP
    component = "2"

    @provide
    def foo(self) -> int:
        return 2

    @provide
    def bar(self, a: int) -> complex:
        return a


class ProviderSum(Provider):
    scope = Scope.APP

    @provide
    def foo(
            self,
            f: Annotated[float, FromComponent("1")],
            c: Annotated[complex, FromComponent("2")],
    ) -> int:
        return int(10 * c + f)


def test_isolated_component():
    container = make_container(Provider1(), Provider2(), ProviderSum())
    assert container.get(int) == 21


class ProviderInc(Provider):
    scope = Scope.APP
    component = "X"

    def __init__(self):
        super().__init__()
        self.value = 1

    @provide
    def foo(self) -> int:
        self.value += 1
        return self.value


def test_cache():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=int)
    provider_inc = ProviderInc()
    container = make_container(provider, provider_inc)
    assert container.get(int, component="X") == 2
    assert container.get(int, component="X") == 2
    assert container.get(int) == 1
    container = make_container(provider, provider_inc)
    assert container.get(int, component="X") == 3
    assert container.get(int, component="X") == 3

    container = make_container(provider_inc.to_component("Y"), provider_inc)
    assert container.get(int, component="X") == 4
    assert container.get(int, component="X") == 4
    assert container.get(int, component="Y") == 5
    assert container.get(int, component="X") == 4
