# Programming Language Landscape

This is a decision map for new projects, not a curriculum. The default is to use a mature ecosystem unless a platform requirement or measured constraint creates a reason to leave it.

**Snapshot:** September 2026.

## Decision tiers

### Tier 1: Default heavy lifters

| Language | Use |
|---|---|
| **Python** | AI, data, automation, application programming interfaces, and rapid product work. Move only measured hot paths elsewhere. |
| **TypeScript** | Browser applications and maintained JavaScript services. Prefer it over untyped JavaScript for product code. |

### Tier 2: Strong next choices

| Language | Use |
|---|---|
| **Go** | Network services, infrastructure, command-line tools, and straightforward concurrency. Choose it when a compiled binary and operational simplicity matter. |
| **Rust** | Native systems, security boundaries, infrastructure, and measured performance work. Its complexity buys real memory and concurrency safety. |

These four languages should handle nearly all new projects.

### Tier 3: Explore and watch

These languages are interesting enough to inspect without manufacturing a production use for them.

| Language | Why it matters | Posture |
|---|---|---|
| **Mojo** | Python-shaped systems language targeting central processing units, graphics processing units, and accelerators. Version 1.0 arrived in August 2026. | Primary watch for AI kernels. The standard library and application binary interface still have important stability limits. |
| **Gleam** | Friendly static types on the Erlang virtual machine and JavaScript runtimes. | The clearest statically typed modern revision of the Erlang idea. Small ecosystem, unusually strong user satisfaction. |
| **Elixir** | Modern dynamic language on the Erlang virtual machine, with Phoenix for web systems and the same supervision model as Erlang. | The practical modern Erlang choice when BEAM fault tolerance is the requirement. Explore and benchmark; do not adopt without a matching workload. |
| **Odin** | Pragmatic, data-oriented C alternative. | Interesting for games and explicit systems work. No reason to learn without a matching project. |
| **Julia** | Interactive scientific computing with native performance. | Mature specialist with strong users. Python remains the broader default. |
| **Zig** | Explicit systems programming, strong C interoperability, cross-compilation, and allocator control. | Prefer Rust unless the requirement is specifically shaped around C, freestanding targets, or Zig's build tooling. |
| **Roc** | Friendly functional language with an application and platform split. | Useful language-design experiment; too early for ordinary projects. |
| **Carbon** | Experimental migration path from C++. | Watch only if it earns credible C++ interoperability and production use. |
| **Vale** | Experiments with native memory safety through generational references. | Watch the memory model, not adoption. |
| **Hare, C3, V, Hylo** | Different attempts at simpler native programming. | Design radar only. |
| **MoonBit, Koka, Unison** | WebAssembly tooling, effect systems, and content-addressed code. | Their ideas may outlive their adoption. |

### Tier 4: Modern but requirement-driven

These are sensible when a platform or domain chooses them for you.

| Language | Strong requirement |
|---|---|
| **Swift** | An Apple-only application. |
| **C#** | .NET, Unity, or a Microsoft-centered organization. |
| **R** | Statistics, biostatistics, and research collaborators. |
| **Dart** | Flutter. |
| **Solidity, Move, Cairo** | A specific smart-contract platform. |
| **CUDA C++ or Triton** | A measured graphics-processing-unit kernel bottleneck. |
| **SQL** | Relational data. SQL is foundational even though it is not an application-language default. |
| **Shell or PowerShell** | Small operating-system or cloud automation at the appropriate platform boundary. |

### Tier 5: Do not use without a strong reason

This tier combines historical languages, oddball paradigms, and ecosystems whose niche can be real without making them good defaults.

#### Functional and concurrent languages

| Language | The strong reason | Read |
|---|---|---|
| **Haskell** | Compilers, formal domain modeling, research, or a team explicitly committed to lazy pure functional programming. | Haskell remains the canonical laboratory for purity, type classes, monads, and algebraic design. There is no universally accepted “modern Haskell.” GHC Haskell itself continues to evolve. OCaml and F# offer more pragmatic strict functional programming; Elm and PureScript adapted related ideas for front-end work; Roc and Koka are newer experiments. Learn the concepts before adopting the ecosystem. |
| **Erlang** | Telecom-style availability, massive numbers of isolated processes, supervision, and recovery from partial failure. | Erlang's modern heirs are **Elixir**, which offers friendlier dynamic syntax and Phoenix, and **Gleam**, which adds static types while retaining the BEAM virtual machine. Use Erlang itself for an installed estate or unusually specific runtime requirements. |
| **OCaml** | Compilers, static analysis, finance, theorem-adjacent tooling, or high-assurance models. | Excellent specialist language with weak general ecosystem pull. |
| **F#** | Functional-first development inside .NET. | A platform-driven specialist. |
| **Clojure** | A committed team wants interactive, immutable, data-oriented Lisp on the Java Virtual Machine. | Powerful model, small ecosystem. |
| **Common Lisp, Scheme, Racket** | Macros, symbolic systems, language design, teaching, or domain-specific languages. | Foundational idea sources, not product defaults. |
| **Standard ML** | Teaching, language research, compiler work, or a required theorem tool. | Historical and academic awareness. |
| **Prolog** | The problem is naturally expressed as facts, relations, and constraint search. | A genuinely different computational model, not a normal application language. |
| **Pony** | Actor concurrency and reference capabilities are the research subject. | Design radar only. |

#### Mainstream and native old guard

| Language | The strong reason |
|---|---|
| **C** | Kernels, firmware, hardware interfaces, embedded targets, or a portable foreign-function boundary. |
| **C++** | A decisive engine, native library, performance estate, or installed codebase. |
| **Java** | A Java organization, Java Virtual Machine estate, or uniquely decisive library. |
| **Kotlin** | Android or an existing Kotlin project. Otherwise excluded by preference. |
| **JavaScript** | Code must execute directly in an untyped JavaScript environment. Maintained application code should normally be TypeScript. |
| **Objective-C** | Existing Apple interoperability. Use Swift for new Apple code. |
| **PHP** | WordPress, Laravel, inexpensive hosting, or an existing PHP property. PHP remains economically important and actively maintained. |
| **Ruby** | An existing Rails product or a team deeply optimized around Rails. |
| **Scala** | An existing Scala system or Apache Spark environment. |
| **Groovy** | Gradle, Jenkins, or an installed Java Virtual Machine automation estate. |
| **Perl** | Maintaining text-processing, bioinformatics, or system scripts. |
| **Lua** | An embedding host such as a game engine, Neovim, or Redis requires it. |
| **Tcl** | Electronic design automation, network equipment, or an installed embedded command language. |
| **Nim, Crystal, D** | An existing project has already made the ecosystem choice. Go and Rust otherwise have stronger gravity. |
| **Assembly** | Boot code, firmware, compilers, cryptography, or a microscopic measured hot path. |
| **Ada or SPARK** | Certification and safety-assurance requirements in aerospace, rail, or defense. |

#### Scientific and institutional languages

| Language | The strong reason |
|---|---|
| **Fortran** | Validated numerical code in weather, physics, fluid dynamics, or high-performance computing. Modern Fortran is not dead; rewriting proven kernels merely because the language is old can destroy value. |
| **MATLAB** | Its engineering toolboxes or Simulink are part of the required workflow. |
| **SAS** | A regulated organization or existing analytics estate requires it. |
| **Stata** | Economics, public health, or social-science collaborators use it. |
| **Wolfram Language** | Symbolic computation or the Wolfram notebook environment is decisive. |

#### Enterprise and historical languages

| Language | The strong reason |
|---|---|
| **COBOL or PL/I** | Maintaining mainframe transaction systems and their embedded business rules. |
| **Pascal, Delphi, Object Pascal** | An installed desktop or industrial codebase. |
| **Visual Basic or BASIC dialects** | Office automation, education, or legacy business software. |
| **ABAP** | SAP. |
| **Apex** | Salesforce. |
| **Smalltalk** | Maintaining an image-based system or studying object-oriented language design. |
| **Forth** | Firmware, a tiny stack machine, or language minimalism is the point. |
| **APL, J, BQN** | Array programming itself is the specialist advantage. |
| **Verilog, SystemVerilog, VHDL** | Designing and verifying digital hardware. These are hardware-description languages rather than software defaults. |

## PHP-adjacent clarification

**Hack** is Meta's typed PHP relative and remains closely tied to HHVM. **FrankenPHP** is a newer Go-based PHP application server, not a replacement language. **Crystal** borrows Ruby-like rather than PHP-specific ergonomics. None changes the tier decision: use PHP when the PHP ecosystem is the requirement.

## Working rule

1. Start with Python or TypeScript.
2. Move to Go for a simpler compiled service or tool.
3. Move to Rust for measured native performance, memory safety, or systems control.
4. Explore Tier 3 only when learning is part of the objective.
5. Enter Tier 4 or Tier 5 only when the platform, codebase, collaborators, or technical domain supply the strong reason.

## Evidence and caveats

The [2025 Stack Overflow survey](https://survey.stackoverflow.co/2025/technology) reported accelerating Python adoption and high admiration for Rust, Gleam, Elixir, and Zig. Admiration measures whether users want to continue, not ecosystem size, hiring depth, or production suitability. Language project pages describe intended strengths rather than independently verified outcomes.

Primary references:

- [Mojo](https://mojolang.org/) and [Mojo 1.0](https://mojolang.org/releases/v1.0.0/)
- [Mojo stability guarantees](https://mojolang.org/docs/api-docs/stability/)
- [Julia](https://julialang.org/)
- [Odin](https://odin-lang.org/)
- [Zig](https://ziglang.org/)
- [Gleam](https://gleam.run/)
- [Roc](https://roc-lang.org/)
- [Carbon](https://github.com/carbon-language/carbon-lang)
