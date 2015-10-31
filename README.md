# typedecl

`typedecl` is a function which, given a type, returns an `std::string` having the
type declaration suitable to be used in a C++ source code.

``` c++
assert(typedecl<int>() == "int");

using PointerToArrayBiDim = char(*)[3][4];
assert(typedecl<PointerToArrayBiDim>() == "char(*)[3][4]");

using ReferenceToFunction = int(&)(char, int[], ...);
assert(typedecl<ReferenceToFunction>() == "int(&)(char, int*, ...)");
```

It may be helpful on programs that generate C++ code or to print messages that help debugging
template issues.

namedecl
--------

There is also a `namedecl` function that returns a type declaration with a name. Such a string
can be used to declare a variable or to define a type alias with `typedef`.

``` c++
assert(namedecl<int>("i") == "int i");
assert(namedecl<char(*)[3][4]>("PoinerToArrayBiDim") == "char(* PoinerToArrayBiDim)[3][4]");
assert(namedecl<int(&)(char, int[], ...)>("callback") == "int(& callback)(char, int*, ...)");
```

Custom Types
------------
In order for `typedecl` to recognize custom types, they must be registered with the `DEFINE_TYPEDECL` macro.

``` c++
class MyClass {
    ...
};

DEFINE_TYPEDECL(MyClass);

void test() {
    assert(typedecl<MyClass>() == "MyClass");
    assert(namedecl<MyClass*[]>("ArrayOfPointersToMyClass") == "MyClass* ArrayOfPointersToMyClass[]");
    assert(typedecl<int(MyClass&)>() == "int(MyClass&)");
}
```
