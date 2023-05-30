from itertools import chain, count
from typing import Iterator, MutableMapping, Optional, TypeVar, Union, overload

try:
    from typing_extensions import assert_never
except ImportError:
    # typing_extenstions is not in the requirements of production
    from typing import NoReturn

    def assert_never(x: NoReturn, /) -> NoReturn:
        assert False, "Expected code to be unreachable"


from .models import (
    Context,
    MonoType,
    PolyType,
    TypeApplication,
    TypeQuantifier,
    TypeVariable,
)


class InferenceError(TypeError):
    pass


T = TypeVar("T", TypeApplication, TypeQuantifier, Context, "Substitution")


class Substitution(dict[str, Union[MonoType, PolyType, Context, "Substitution"]]):
    """S = { αᵢ ↦ τᵢ }

    a Mapping of names alpha to types tau
    """

    @overload
    def __call__(self, value: TypeVariable) -> MonoType:
        ...

    @overload
    def __call__(self, value: T) -> T:
        ...

    def __call__(self, value):
        "apply substitution"
        match value:
            case Context():
                # apply to all types in the context
                return Context({k: self(v) for k, v in value.items()})
            case TypeApplication(c, taus):
                return TypeApplication(c, tuple(self(t) for t in taus))
            case TypeQuantifier(alpha, sigma):
                return TypeQuantifier(alpha, self(sigma))
            case TypeVariable(alpha):
                return self.get(alpha, value)
            case Substitution(s2):
                # merge self with s2
                return Substitution(
                    chain(
                        self.items(),  #
                        ((a, self(t)) for a, t in s2.items()),
                    )
                )
            case _ as unreachable:
                assert_never(unreachable)


def unify(a: MonoType, b: MonoType) -> Substitution:
    match a, b:
        case TypeVariable(aa), TypeVariable(ab):
            if aa == ab:
                # same typevar -> empty substitution
                return Substitution()

        # XXX: lazy handling of Either for M
        # case TypeApplication("Either", taus), _:
        #     if any(isinstance(t, TypeVariable) for t in taus):
        #         # postpone unification until types are inferred
        #         return Substitution()
        #     s1 = unify(taus[0], b)
        #     s2 = unify(taus[1], b)
        #     return s1(s2)
        # case _, TypeApplication("Either", taus):
        #     # flip a and b
        #     return unify(b, a)
        #
        # TODO: Either a b should unify with Either b a
        case TypeApplication(ca, ta), TypeApplication(cb, tb):
            if ca != cb:
                raise InferenceError(
                    f"Can't unify types {a} and {b}: different type functions"
                )
            if len(ta) != len(tb):
                raise InferenceError(
                    f"Can't unify types {a} and {b}: different number of arguments"
                )
            s = Substitution()
            for t1, t2 in zip(ta, tb):
                s = s(unify(s(t1), s(t2)))
            return s

    if isinstance(a, TypeVariable):
        if a in b:
            raise InferenceError(
                f"Can't unify: {a} occurs in {b} so unifying would create infinite type"
            )
        return Substitution(**{a.alpha: b})

    if isinstance(b, TypeVariable):
        # a is not a TypeVar b is -> flip
        return unify(b, a)

    raise ValueError("Unify is unable to handle inputs {a} and {b}")


def free_variables(value: Context | PolyType) -> set[str]:
    # TODO handle expression?
    match value:
        case TypeVariable(a):
            # free(α) = {α}
            return {a}
        case TypeApplication(_, taus):
            # free(Cτ₁...τₙ) = ⋃ free(τᵢ) for i in 1..n
            # union of all free in taus
            return set().union(*(free_variables(t) for t in taus))
        case Context():
            # free(Γ) = ⋃ free(σ) ∀ σ ∊ Γ
            return set().union(*(free_variables(s) for s in value.values()))
        case TypeQuantifier(a, s):
            # alpha is bound in sigma
            return free_variables(s) - {a}
        case _ as unreachable:
            assert_never(unreachable)


def generalise(context: Context, t: MonoType) -> PolyType:
    quantifiers = free_variables(t).difference(free_variables(context))
    s: PolyType = t
    for q in quantifiers:
        s = TypeQuantifier(alpha=q, sigma=s)
    return s


def gen_type_vars() -> Iterator[TypeVariable]:
    for i in count():
        yield TypeVariable(alpha=f"t{i}")


def instantiate(
    t: PolyType,
    mapping: Optional[MutableMapping[str, TypeVariable]] = None,
    type_vars: Iterator[TypeVariable] = gen_type_vars(),
) -> MonoType:
    def inst(t, m) -> MonoType:
        return instantiate(t, m, type_vars)

    if mapping is None:
        mapping = {}
    match t:
        case TypeVariable(a):
            return mapping.get(a, t)
        case TypeApplication(C=c, taus=taus):
            # ignore because of https://github.com/python/mypy/issues/7509
            return TypeApplication(c, tuple(inst(t, mapping) for t in taus))  # type: ignore
        case TypeQuantifier(a, s):
            mapping[a] = next(type_vars)
            return inst(s, mapping)
        case _ as unreachable:
            assert_never(unreachable)


def f(*taus: MonoType) -> TypeApplication:
    """A helper function to create a TypeApplication with arbitrary number of arguments."""
    match taus:
        case [t1, t2]:
            return TypeApplication("->", (t1, t2))
        case [t1, t2, t3, *rest]:
            return TypeApplication("->", (t1, f(t2, t3, *rest)))
        case _:
            raise ValueError("Missing arguments, need to pass at least 2 MonoTypes")


def array(t: MonoType) -> TypeApplication:
    return TypeApplication("[]", (t,))


def either(a: MonoType, b: MonoType) -> TypeApplication:
    return TypeApplication("Either", (a, b))
