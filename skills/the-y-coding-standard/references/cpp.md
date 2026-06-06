# C++ Standards (the_y_coding_standard)

## When to load this file

Load this reference when working with:
- Any `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hh`, `.hxx`, or `.h` file in a C++ project.
- CMake projects (`CMakeLists.txt`, `*.cmake`).
- Embedded systems, firmware, or microcontroller code.
- Performance-critical code paths where cycles and cache lines matter.
- Game engines, real-time systems, graphics, audio DSP, robotics.
- Native library bindings (NAPI, JNI, Python C-extensions).
- Anywhere the user mentions "C++", "modern C++", "RAII", "templates", or "CMake".

For object-oriented design rules (SOLID, rule-of-zero, rule-of-five), also load `oop.md`.

## Compilation Standard

Target **C++20 minimum**. Prefer **C++23** where the toolchain supports it (recent GCC 13+, Clang 17+, MSVC 19.37+). Drop anything older. C++14 and C++17 are legacy.

When scaffolding a new project, verify current compiler support via the cppreference compiler support matrix. Pick the standard the team's CI compiler can hit, not the latest paper feature.

```cmake
cmake_minimum_required(VERSION 3.25)
project(MyProject LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compile commands for clangd, clang-tidy, IDEs.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Warnings are errors. Always.
if(MSVC)
    add_compile_options(/W4 /WX /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror -Wshadow -Wconversion)
endif()
```

## Build System

**CMake 3.25+ only.** No hand-rolled Makefiles. No `autotools`. No Bazel unless the org already runs it.

- One root `CMakeLists.txt`. Subdirectories use `add_subdirectory()`.
- Use modern target-based CMake. `target_link_libraries`, `target_include_directories`, `target_compile_features`. Never global `include_directories` or `link_libraries`.
- Export package config so downstream consumers can `find_package()` you.
- Presets via `CMakePresets.json` for debug, release, asan, tsan, ubsan, coverage.

## Package Management

Pick one. Pin versions. Commit the lockfile.

- **vcpkg** (manifest mode) for most projects. `vcpkg.json` at repo root.
- **Conan 2.x** when the team needs binary caching or non-Microsoft ecosystem.

Never copy-paste third-party source into `third_party/` unless it is unmaintained and tiny. Fetch via the package manager, not git submodules.

## Project Structure

```
project/
├── CMakeLists.txt
├── CMakePresets.json
├── vcpkg.json                  # or conanfile.py
├── .clang-format
├── .clang-tidy
├── include/
│   └── myproject/
│       ├── core/
│       │   ├── engine.hpp
│       │   ├── engine_config.hpp      # config struct, separate file
│       │   ├── engine_state.hpp       # enum, separate file
│       │   └── engine_constants.hpp   # constexpr constants, separate file
│       └── net/
│           └── client.hpp
├── src/
│   ├── core/
│   │   └── engine.cpp
│   └── net/
│       └── client.cpp
├── tests/
│   ├── CMakeLists.txt
│   └── core/
│       └── engine_test.cpp
├── fuzz/
│   └── parser_fuzz.cpp
└── cmake/
    └── modules/
```

## Yash Modularity Rules

Reuse the same separation-by-feature discipline as the TypeScript and Python guides.

1. **Enums in their own headers.** `engine_state.hpp` holds `enum class EngineState`. Nothing else.
2. **Constants in their own headers.** `engine_constants.hpp` holds `inline constexpr` values. No logic.
3. **Config structs in their own headers.** Plain-old-data structs that configure a feature live next to the feature, not bundled into the main class header.
4. **One class per `.hpp` + `.cpp` pair.** Never dump two unrelated classes in one file.
5. **Group by feature, not by kind.** `include/myproject/auth/` contains the auth class, its enum, its constants, its config. Do not split into `enums/`, `constants/`, `classes/` top-level dirs.
6. **PIMPL when ABI stability matters or when the header pulls heavy includes.**

## Header Hygiene

- Always `#pragma once`. Skip include guards.
- Headers declare. Source files define.
- Forward-declare before you `#include`. Keep header dependencies minimal.
- Never `using namespace std;` in a header. Tolerated inside a `.cpp` if scoped to a function.
- Public API headers go under `include/<project>/`. Private headers stay next to the `.cpp` in `src/`.

```cpp
// engine.hpp
#pragma once

#include <memory>
#include <string>

#include "myproject/core/engine_config.hpp"
#include "myproject/core/engine_state.hpp"

namespace myproject::core {

class Logger;  // forward declare. do not include logger.hpp here.

class Engine {
public:
    explicit Engine(EngineConfig config);
    ~Engine();

    // Rule of five. See oop.md for full discussion.
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    Engine(Engine&&) noexcept;
    Engine& operator=(Engine&&) noexcept;

    [[nodiscard]] EngineState state() const noexcept;
    [[nodiscard]] std::expected<void, std::string> start();
    void stop() noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace myproject::core
```

## Namespaces

- Top-level namespace matches the project: `namespace myproject {}`.
- Sub-namespaces for subsystems: `myproject::core`, `myproject::net`, `myproject::auth`.
- Nested namespace syntax: `namespace myproject::core { ... }`.
- Anonymous namespaces inside `.cpp` for translation-unit-local helpers.

## Memory and Ownership

Raw `new` and `delete` are banned in user code. Period. Smart pointers always.

- `std::unique_ptr<T>` for single ownership. Default choice.
- `std::shared_ptr<T>` only when ownership is genuinely shared. Reach for it second.
- `std::weak_ptr<T>` to break cycles.
- Stack allocation when lifetime is bounded by scope.
- `std::pmr` allocators when you need custom memory pools.

```cpp
// Wrong.
MyObject* obj = new MyObject();
// ... code that might throw ...
delete obj;  // never runs if an exception escapes.

// Right.
auto obj = std::make_unique<MyObject>();
// destructor runs at scope exit no matter what.
```

`new` and `delete` are acceptable inside the implementation of a custom allocator, an intrusive container, or a low-level FFI boundary. Document why. Otherwise: forbidden.

## Rule of Zero, Rule of Five

See `oop.md`. Short version:

- Default: write zero special member functions. Let the compiler synthesize them. This is the **rule of zero**.
- If you must write one of {destructor, copy ctor, copy assign, move ctor, move assign}, declare all five. This is the **rule of five**.
- Delete copy or move explicitly when the class is not copyable or movable.

## Error Handling

Prefer **`std::expected<T, E>`** (C++23) and **`std::optional<T>`** for recoverable, expected failures. Exceptions are for truly exceptional, unrecoverable conditions or across library boundaries where the cost of unwinding is acceptable.

In embedded, real-time, or `-fno-exceptions` codebases: exceptions are off entirely. `std::expected` is the only path.

```cpp
// Good. Recoverable miss. No exception needed.
[[nodiscard]] std::optional<User> UserRepository::find_by_id(std::uint64_t id) const {
    if (const auto it = users_.find(id); it != users_.end()) {
        return it->second;
    }
    return std::nullopt;
}

// Good. Operation that can fail with a structured error.
[[nodiscard]] std::expected<Connection, NetError> connect(const Endpoint& ep);

// Caller.
auto conn = connect(ep);
if (!conn) {
    log_error(conn.error());
    return;
}
use(*conn);
```

Never silently swallow an error code. Never log-and-continue without a justification in a comment.

## Const Correctness

- Every method that does not mutate observable state is `const`.
- Pass non-owning, non-mutating parameters by `const&`.
- Mark variables `const` or `constexpr` if they never change after initialization.
- Use `std::string_view` for read-only string parameters. Use `std::span<const T>` for read-only contiguous ranges.
- Combine with `noexcept` where the function genuinely cannot throw. The compiler uses both.

## `[[nodiscard]]`

Put `[[nodiscard]]` on every return value that matters. If a caller ignoring the result would be a bug, mark it. Examples: getters, factory functions, error-returning functions, anything returning `std::expected` or `std::optional`.

```cpp
[[nodiscard]] std::expected<Frame, DecodeError> decode_next();
[[nodiscard]] bool is_open() const noexcept;
[[nodiscard]] std::size_t size() const noexcept;
```

## Modern Features to Use

- `auto` when the type is obvious or unwieldy. Not for everything.
- Range-based `for` loops by default. Indexed loops only when you need the index.
- `constexpr`, `consteval`, `constinit` for compile-time work.
- `std::optional<T>` instead of sentinel values.
- `std::variant<T, U>` for closed sums. `std::expected<T, E>` for fallible returns.
- Structured bindings: `auto [key, value] = entry;`.
- `std::string_view`, `std::span<T>` for non-owning views.
- Concepts and `requires` clauses instead of SFINAE.
- Designated initializers: `Config{.timeout = 30s, .retries = 3}`.
- `<format>` and `std::print` (C++23) instead of `printf` or stream manipulators.
- Ranges and views for collection pipelines.

## Naming

| Thing | Convention | Example |
|---|---|---|
| Classes, structs, enums | PascalCase | `NetworkManager`, `EngineState` |
| Enum values | PascalCase | `EngineState::Running` |
| Functions, methods | snake_case | `get_user_by_id` |
| Variables | snake_case | `user_count` |
| `constexpr` and constants | kPascalCase | `kMaxConnections` |
| Member variables | trailing `_` | `name_`, `count_` |
| Namespaces | lowercase | `myproject::core` |
| Template parameters | PascalCase | `template <typename T, std::size_t N>` |
| Macros (avoid) | SCREAMING_SNAKE | `MY_ASSERT(x)` |

## No Magic Numbers, No Magic Strings

```cpp
// Wrong.
if (retries > 3) { /* ... */ }

// Right.
inline constexpr int kMaxRetries = 3;
if (retries > kMaxRetries) { /* ... */ }
```

Constants live in a feature-scoped header (`engine_constants.hpp`), not scattered across the implementation.

## Tooling and CI

Non-negotiable. All of these run on every PR.

- **clang-format** with a project `.clang-format` (start from LLVM or Google, then tune).
- **clang-tidy** with checks enabled: `bugprone-*`, `cert-*`, `cppcoreguidelines-*`, `modernize-*`, `performance-*`, `readability-*`. Treat warnings as errors.
- **cppcheck** as a second linter. It catches different things than clang-tidy.
- **Sanitizers** in CI: AddressSanitizer, UndefinedBehaviorSanitizer, ThreadSanitizer (for concurrent code). Build a sanitizer preset.
- **Compiler warnings** at `-Wall -Wextra -Wpedantic -Werror` on GCC/Clang and `/W4 /WX` on MSVC.
- **include-what-you-use** to keep headers honest.

## Testing

- **Google Test** or **Catch2 v3**. Pick one per repo. Stick with it.
- Tests live under `tests/` mirroring the `src/` tree.
- Each test target is its own CMake executable so failures isolate cleanly.
- Use `CTest` as the runner. `ctest --output-on-failure` in CI.
- Aim for fast unit tests. Integration tests in a separate target.

```cmake
# tests/CMakeLists.txt
find_package(GTest REQUIRED)
add_executable(engine_test core/engine_test.cpp)
target_link_libraries(engine_test PRIVATE myproject::core GTest::gtest_main)
add_test(NAME engine_test COMMAND engine_test)
```

### Fuzz Testing

Any code that parses bytes from an untrusted source ships with a fuzzer. Non-negotiable.

- libFuzzer (Clang) or AFL++. libFuzzer is the default if Clang is in CI.
- Each fuzzer is its own executable in `fuzz/`.
- Seed corpora live in `fuzz/corpus/<target>/`.
- Run fuzzers in CI for a bounded budget on every PR. Run longer fuzz campaigns nightly.

```cpp
// fuzz/parser_fuzz.cpp
#include "myproject/parser.hpp"
extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    myproject::parse({reinterpret_cast<const char*>(data), size});
    return 0;
}
```

## Concurrency

- `std::thread`, `std::jthread` (prefer `jthread` for the auto-join).
- `std::mutex`, `std::shared_mutex`, `std::scoped_lock`. Never bare `lock()` / `unlock()`.
- `std::atomic<T>` only when you understand the memory order you are asking for.
- Coroutines (`co_await`, `co_return`) for async pipelines.
- Pin shared state behind a mutex or move it across threads. No raw shared mutable state.
- Run ThreadSanitizer in CI for any code with more than one thread.

## When this reference loads

This file activates automatically when the agent detects:

- Files matching `*.cpp`, `*.cc`, `*.cxx`, `*.hpp`, `*.hh`, `*.hxx`, `*.h`.
- A `CMakeLists.txt`, `CMakePresets.json`, `vcpkg.json`, or `conanfile.py` at any level.
- A `.clang-format` or `.clang-tidy` in the repo.
- Discussions of RAII, templates, smart pointers, the C++ standard library, or game/embedded/graphics code.

Pair it with `oop.md` for class-design questions (SOLID, composition vs inheritance, rule-of-zero, rule-of-five). Pair it with the testing reference when wiring CI.
